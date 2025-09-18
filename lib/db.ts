import { PrismaClient } from '@prisma/client'

// Global variable for Prisma client in development
declare global {
  var prisma: PrismaClient | undefined
}

// Create a single instance of Prisma Client
export const prisma =
  globalThis.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
    errorFormat: 'pretty',
    datasources: {
      db: {
        url: process.env.DATABASE_URL,
      },
    },
  })

// Prevent multiple instances during hot reload in development
if (process.env.NODE_ENV !== 'production') globalThis.prisma = prisma

// Database utility functions
export const dbUtils = {
  // Connection health check
  async healthCheck() {
    try {
      await prisma.$queryRaw`SELECT 1`
      return { status: 'healthy', timestamp: new Date().toISOString() }
    } catch (error) {
      console.error('Database health check failed:', error)
      return { status: 'unhealthy', error: error.message, timestamp: new Date().toISOString() }
    }
  },

  // Get database statistics
  async getStats() {
    try {
      const [users, issues, solutions, categories] = await Promise.all([
        prisma.user.count(),
        prisma.issue.count(),
        prisma.solution.count(),
        prisma.category.count(),
      ])

      return {
        users,
        issues,
        solutions,
        categories,
        timestamp: new Date().toISOString(),
      }
    } catch (error) {
      console.error('Error fetching database stats:', error)
      throw error
    }
  },

  // Clean up expired sessions
  async cleanupExpiredSessions() {
    try {
      const result = await prisma.session.deleteMany({
        where: {
          expires: {
            lt: new Date(),
          },
        },
      })
      return result.count
    } catch (error) {
      console.error('Error cleaning up expired sessions:', error)
      throw error
    }
  },

  // Search issues with full-text search
  async searchIssues(query: string, options: {
    categoryId?: string
    severity?: string
    status?: string
    technologies?: string[]
    limit?: number
    offset?: number
  } = {}) {
    const {
      categoryId,
      severity,
      status,
      technologies,
      limit = 20,
      offset = 0,
    } = options

    try {
      const where: any = {
        AND: [
          query ? {
            OR: [
              { title: { contains: query, mode: 'insensitive' } },
              { description: { contains: query, mode: 'insensitive' } },
              { errorMessage: { contains: query, mode: 'insensitive' } },
            ],
          } : {},
          categoryId ? { categoryId } : {},
          severity ? { severity } : {},
          status ? { status } : {},
          technologies && technologies.length > 0 ? {
            technologies: {
              some: {
                name: { in: technologies },
              },
            },
          } : {},
        ].filter(condition => Object.keys(condition).length > 0),
      }

      const [issues, total] = await Promise.all([
        prisma.issue.findMany({
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
            category: true,
            technologies: true,
            solutions: {
              where: { isAccepted: true },
              select: {
                id: true,
                title: true,
                effectiveness: true,
              },
            },
            _count: {
              select: {
                solutions: true,
                comments: true,
              },
            },
          },
          orderBy: [
            { upvotes: 'desc' },
            { createdAt: 'desc' },
          ],
          take: limit,
          skip: offset,
        }),
        prisma.issue.count({ where }),
      ])

      return {
        issues,
        total,
        hasMore: offset + limit < total,
        page: Math.floor(offset / limit) + 1,
        totalPages: Math.ceil(total / limit),
      }
    } catch (error) {
      console.error('Error searching issues:', error)
      throw error
    }
  },

  // Get similar issues based on title and description
  async getSimilarIssues(issueId: string, title: string, description: string, limit = 5) {
    try {
      // Simple similarity search using PostgreSQL's similarity functions
      // In production, you might want to use a more sophisticated approach like vector embeddings
      const issues = await prisma.issue.findMany({
        where: {
          id: { not: issueId },
          OR: [
            {
              title: {
                contains: title.split(' ').slice(0, 3).join(' '),
                mode: 'insensitive',
              },
            },
            {
              description: {
                contains: description.split(' ').slice(0, 5).join(' '),
                mode: 'insensitive',
              },
            },
          ],
          status: 'RESOLVED',
        },
        include: {
          category: true,
          technologies: true,
          solutions: {
            where: { isAccepted: true },
            select: {
              id: true,
              title: true,
              effectiveness: true,
            },
            take: 1,
          },
        },
        orderBy: {
          upvotes: 'desc',
        },
        take: limit,
      })

      return issues
    } catch (error) {
      console.error('Error finding similar issues:', error)
      throw error
    }
  },

  // Log search queries for analytics
  async logSearch(query: string, results: number, userId?: string, userAgent?: string, ipAddress?: string) {
    try {
      await prisma.searchLog.create({
        data: {
          query,
          results,
          userId,
          userAgent,
          ipAddress,
        },
      })
    } catch (error) {
      console.error('Error logging search:', error)
      // Don't throw error for logging failures
    }
  },

  // Get trending searches
  async getTrendingSearches(limit = 10, days = 7) {
    try {
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - days)

      const trends = await prisma.searchLog.groupBy({
        by: ['query'],
        where: {
          createdAt: {
            gte: startDate,
          },
          results: {
            gt: 0,
          },
        },
        _count: {
          query: true,
        },
        orderBy: {
          _count: {
            query: 'desc',
          },
        },
        take: limit,
      })

      return trends.map(trend => ({
        query: trend.query,
        count: trend._count.query,
      }))
    } catch (error) {
      console.error('Error fetching trending searches:', error)
      throw error
    }
  },
}

// Graceful shutdown
process.on('beforeExit', async () => {
  await prisma.$disconnect()
})

export default prisma