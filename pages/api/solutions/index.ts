import { NextApiRequest, NextApiResponse } from 'next'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'
import { z } from 'zod'
import { ApiResponse } from '@/types'

// Validation schema
const createSolutionSchema = z.object({
  title: z.string().min(5, 'Title must be at least 5 characters'),
  description: z.string().min(20, 'Description must be at least 20 characters'),
  codeSnippet: z.string().optional(),
  steps: z.array(z.string().min(1)).min(1, 'At least one step is required'),
  issueId: z.string().uuid('Invalid issue ID'),
})

const querySchema = z.object({
  issueId: z.string().uuid().optional(),
  page: z.string().transform((val) => parseInt(val) || 1).optional(),
  limit: z.string().transform((val) => Math.min(parseInt(val) || 20, 50)).optional(),
})

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse>
) {
  const session = await getServerSession(req, res, authOptions)

  if (req.method === 'GET') {
    try {
      const query = querySchema.parse(req.query)
      const { issueId, page = 1, limit = 20 } = query
      const offset = (page - 1) * limit

      // Build where clause
      const where = issueId ? { issueId } : {}

      // Fetch solutions with pagination
      const [solutions, total] = await Promise.all([
        prisma.solution.findMany({
          where,
          include: {
            author: {
              select: {
                id: true,
                name: true,
                email: true,
                image: true,
              },
            },
            issue: {
              select: {
                id: true,
                title: true,
                status: true,
              },
            },
          },
          orderBy: [
            { isAccepted: 'desc' },
            { upvotes: 'desc' },
            { createdAt: 'desc' },
          ],
          take: limit,
          skip: offset,
        }),
        prisma.solution.count({ where }),
      ])

      res.status(200).json({
        success: true,
        data: solutions,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
          hasMore: offset + limit < total,
        },
      })
    } catch (error) {
      console.error('Error fetching solutions:', error)
      
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          success: false,
          error: 'Invalid query parameters',
        })
      }

      res.status(500).json({
        success: false,
        error: 'Failed to fetch solutions',
      })
    }
  }

  else if (req.method === 'POST') {
    // Authentication required
    if (!session) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
      })
    }

    try {
      // Validate request body
      const validatedData = createSolutionSchema.parse(req.body)

      // Check if issue exists
      const issue = await prisma.issue.findUnique({
        where: { id: validatedData.issueId },
        select: { id: true, status: true, authorId: true },
      })

      if (!issue) {
        return res.status(404).json({
          success: false,
          error: 'Issue not found',
        })
      }

      // Create solution
      const solution = await prisma.solution.create({
        data: {
          ...validatedData,
          authorId: session.user.id,
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
          issue: {
            select: {
              id: true,
              title: true,
              status: true,
            },
          },
        },
      })

      // If this is the first solution and the issue is still open, update status
      if (issue.status === 'OPEN') {
        await prisma.issue.update({
          where: { id: validatedData.issueId },
          data: { status: 'IN_PROGRESS' },
        })
      }

      res.status(201).json({
        success: true,
        data: solution,
        message: 'Solution created successfully',
      })
    } catch (error) {
      console.error('Error creating solution:', error)

      if (error instanceof z.ZodError) {
        return res.status(400).json({
          success: false,
          error: 'Validation error',
          message: error.errors[0].message,
        })
      }

      res.status(500).json({
        success: false,
        error: 'Failed to create solution',
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