import { NextApiRequest, NextApiResponse } from 'next'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '@/lib/auth'
import { prisma, dbUtils } from '@/lib/db'
import { z } from 'zod'
import { ApiResponse, CreateIssueData, SearchFilters } from '@/types'

// Validation schemas
const createIssueSchema = z.object({
  title: z.string().min(5, 'Title must be at least 5 characters'),
  description: z.string().min(20, 'Description must be at least 20 characters'),
  errorMessage: z.string().optional(),
  codeSnippet: z.string().optional(),
  stackTrace: z.string().optional(),
  severity: z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
  categoryId: z.string().uuid('Invalid category ID'),
  technologies: z.array(z.string()).min(1, 'At least one technology is required'),
  environment: z.string().optional(),
})

const querySchema = z.object({
  page: z.string().transform((val) => parseInt(val) || 1).optional(),
  limit: z.string().transform((val) => Math.min(parseInt(val) || 20, 100)).optional(),
  q: z.string().optional(),
  category: z.string().optional(),
  severity: z.string().optional(),
  status: z.string().optional(),
  tech: z.union([z.string(), z.array(z.string())]).optional(),
  author: z.string().optional(),
  sort: z.enum(['created', 'updated', 'upvotes', 'views']).optional(),
  order: z.enum(['asc', 'desc']).optional(),
})

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse>
) {
  const session = await getServerSession(req, res, authOptions)

  if (req.method === 'GET') {
    try {
      // Parse and validate query parameters
      const query = querySchema.parse(req.query)
      const { page = 1, limit = 20, q, category, severity, status, tech, author, sort = 'created', order = 'desc' } = query

      // Build search filters
      const filters: SearchFilters = {
        query: q,
        categoryId: category,
        severity: severity as any,
        status: status as any,
        technologies: Array.isArray(tech) ? tech : tech ? [tech] : undefined,
        authorId: author,
        sortBy: sort,
        sortOrder: order,
      }

      // Calculate offset
      const offset = (page - 1) * limit

      // Perform search
      const result = await dbUtils.searchIssues(q || '', {
        ...filters,
        limit,
        offset,
      })

      // Log search for analytics
      await dbUtils.logSearch(
        q || '',
        result.total,
        session?.user?.id,
        req.headers['user-agent'],
        req.headers['x-forwarded-for'] as string || req.connection.remoteAddress
      )

      res.status(200).json({
        success: true,
        data: result.issues,
        pagination: {
          page: result.page,
          limit,
          total: result.total,
          totalPages: result.totalPages,
          hasMore: result.hasMore,
        },
      })
    } catch (error) {
      console.error('Error fetching issues:', error)
      
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          success: false,
          error: 'Invalid query parameters',
          message: error.errors[0].message,
        })
      }

      res.status(500).json({
        success: false,
        error: 'Failed to fetch issues',
      })
    }
  }

  else if (req.method === 'POST') {
    // Authentication required for creating issues
    if (!session) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
      })
    }

    try {
      // Validate request body
      const validatedData = createIssueSchema.parse(req.body)
      const { technologies, ...issueData } = validatedData

      // Start transaction
      const result = await prisma.$transaction(async (tx) => {
        // Find or create technologies
        const techRecords = await Promise.all(
          technologies.map(async (techName) => {
            return await tx.technology.upsert({
              where: { name: techName.toLowerCase() },
              update: {},
              create: { name: techName.toLowerCase() },
            })
          })
        )

        // Create the issue
        const issue = await tx.issue.create({
          data: {
            ...issueData,
            authorId: session.user.id,
            technologies: {
              connect: techRecords.map((tech) => ({ id: tech.id })),
            },
          },
          include: {
            author: {
              select: {
                id: true,
                name: true,
                email: true,
                image: true,
              },
            },
            category: true,
            technologies: true,
            solutions: {
              include: {
                author: {
                  select: {
                    id: true,
                    name: true,
                    email: true,
                    image: true,
                  },
                },
              },
            },
            comments: {
              include: {
                author: {
                  select: {
                    id: true,
                    name: true,
                    email: true,
                    image: true,
                  },
                },
              },
            },
            _count: {
              select: {
                solutions: true,
                comments: true,
                aiSuggestions: true,
              },
            },
          },
        })

        return issue
      })

      res.status(201).json({
        success: true,
        data: result,
        message: 'Issue created successfully',
      })
    } catch (error) {
      console.error('Error creating issue:', error)

      if (error instanceof z.ZodError) {
        return res.status(400).json({
          success: false,
          error: 'Validation error',
          message: error.errors[0].message,
        })
      }

      res.status(500).json({
        success: false,
        error: 'Failed to create issue',
      })
    }
  }

  else {
    res.status(405).json({
      success: false,
      error: 'Method not allowed',
    })
  }
}

// Helper function to build order by clause
function buildOrderBy(sort: string, order: string) {
  const orderBy: any = {}
  
  switch (sort) {
    case 'created':
      orderBy.createdAt = order
      break
    case 'updated':
      orderBy.updatedAt = order
      break
    case 'upvotes':
      orderBy.upvotes = order
      break
    case 'views':
      orderBy.views = order
      break
    default:
      orderBy.createdAt = 'desc'
  }

  return orderBy
}