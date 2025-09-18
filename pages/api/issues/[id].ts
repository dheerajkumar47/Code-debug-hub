import { NextApiRequest, NextApiResponse } from 'next'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'
import { z } from 'zod'
import { ApiResponse } from '@/types'

// Validation schema for updates
const updateIssueSchema = z.object({
  title: z.string().min(5).optional(),
  description: z.string().min(20).optional(),
  errorMessage: z.string().optional(),
  codeSnippet: z.string().optional(),
  stackTrace: z.string().optional(),
  severity: z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']).optional(),
  status: z.enum(['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']).optional(),
  categoryId: z.string().uuid().optional(),
  technologies: z.array(z.string()).optional(),
  environment: z.string().optional(),
})

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse>
) {
  const { id } = req.query
  const session = await getServerSession(req, res, authOptions)

  if (typeof id !== 'string') {
    return res.status(400).json({
      success: false,
      error: 'Invalid issue ID',
    })
  }

  if (req.method === 'GET') {
    try {
      // Increment view count
      await prisma.issue.update({
        where: { id },
        data: { views: { increment: 1 } },
      })

      // Fetch issue with all relations
      const issue = await prisma.issue.findUnique({
        where: { id },
        include: {
          author: {
            select: {
              id: true,
              name: true,
              email: true,
              image: true,
              role: true,
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
            orderBy: [
              { isAccepted: 'desc' },
              { upvotes: 'desc' },
              { createdAt: 'asc' },
            ],
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
            orderBy: { createdAt: 'asc' },
          },
          aiSuggestions: {
            orderBy: { createdAt: 'desc' },
            take: 1, // Only get the latest AI suggestion
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

      if (!issue) {
        return res.status(404).json({
          success: false,
          error: 'Issue not found',
        })
      }

      res.status(200).json({
        success: true,
        data: issue,
      })
    } catch (error) {
      console.error('Error fetching issue:', error)
      res.status(500).json({
        success: false,
        error: 'Failed to fetch issue',
      })
    }
  }

  else if (req.method === 'PUT') {
    // Authentication required
    if (!session) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
      })
    }

    try {
      // Check if issue exists and user has permission
      const existingIssue = await prisma.issue.findUnique({
        where: { id },
        select: { authorId: true },
      })

      if (!existingIssue) {
        return res.status(404).json({
          success: false,
          error: 'Issue not found',
        })
      }

      // Check permission (only author or admin/moderator can edit)
      const canEdit = existingIssue.authorId === session.user.id || 
                     ['ADMIN', 'MODERATOR'].includes(session.user.role)

      if (!canEdit) {
        return res.status(403).json({
          success: false,
          error: 'Not authorized to edit this issue',
        })
      }

      // Validate request body
      const validatedData = updateIssueSchema.parse(req.body)
      const { technologies, ...updateData } = validatedData

      // Update issue in transaction
      const updatedIssue = await prisma.$transaction(async (tx) => {
        // Update technologies if provided
        if (technologies) {
          // Disconnect all existing technologies
          await tx.issue.update({
            where: { id },
            data: {
              technologies: {
                set: [], // Clear all connections
              },
            },
          })

          // Find or create new technologies
          const techRecords = await Promise.all(
            technologies.map(async (techName) => {
              return await tx.technology.upsert({
                where: { name: techName.toLowerCase() },
                update: {},
                create: { name: techName.toLowerCase() },
              })
            })
          )

          // Connect new technologies
          await tx.issue.update({
            where: { id },
            data: {
              technologies: {
                connect: techRecords.map((tech) => ({ id: tech.id })),
              },
            },
          })
        }

        // Update other fields
        return await tx.issue.update({
          where: { id },
          data: updateData,
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
      })

      res.status(200).json({
        success: true,
        data: updatedIssue,
        message: 'Issue updated successfully',
      })
    } catch (error) {
      console.error('Error updating issue:', error)

      if (error instanceof z.ZodError) {
        return res.status(400).json({
          success: false,
          error: 'Validation error',
          message: error.errors[0].message,
        })
      }

      res.status(500).json({
        success: false,
        error: 'Failed to update issue',
      })
    }
  }

  else if (req.method === 'DELETE') {
    // Authentication required
    if (!session) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
      })
    }

    try {
      // Check if issue exists and user has permission
      const existingIssue = await prisma.issue.findUnique({
        where: { id },
        select: { authorId: true },
      })

      if (!existingIssue) {
        return res.status(404).json({
          success: false,
          error: 'Issue not found',
        })
      }

      // Check permission (only author or admin can delete)
      const canDelete = existingIssue.authorId === session.user.id || 
                       session.user.role === 'ADMIN'

      if (!canDelete) {
        return res.status(403).json({
          success: false,
          error: 'Not authorized to delete this issue',
        })
      }

      // Delete issue (cascade will handle related records)
      await prisma.issue.delete({
        where: { id },
      })

      res.status(200).json({
        success: true,
        message: 'Issue deleted successfully',
      })
    } catch (error) {
      console.error('Error deleting issue:', error)
      res.status(500).json({
        success: false,
        error: 'Failed to delete issue',
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