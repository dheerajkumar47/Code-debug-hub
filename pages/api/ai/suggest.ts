import { NextApiRequest, NextApiResponse } from 'next'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '@/lib/auth'
import { aiSuggestionService } from '@/lib/openai'
import { prisma, dbUtils } from '@/lib/db'
import { z } from 'zod'
import { ApiResponse, AISuggestionRequest } from '@/types'

// Validation schema
const suggestionRequestSchema = z.object({
  issueId: z.string().uuid('Invalid issue ID'),
  useCache: z.boolean().optional().default(true),
})

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
    })
  }

  const session = await getServerSession(req, res, authOptions)

  // Authentication required
  if (!session) {
    return res.status(401).json({
      success: false,
      error: 'Authentication required',
    })
  }

  try {
    // Validate request body
    const { issueId, useCache } = suggestionRequestSchema.parse(req.body)

    // Check rate limiting
    const canRequest = await aiSuggestionService.checkRateLimit(session.user.id)
    if (!canRequest) {
      return res.status(429).json({
        success: false,
        error: 'Rate limit exceeded',
        message: 'Maximum AI suggestions per hour reached. Please try again later.',
      })
    }

    // Check for cached suggestion first
    if (useCache) {
      const cachedSuggestion = await aiSuggestionService.getCachedSuggestion(issueId)
      if (cachedSuggestion) {
        return res.status(200).json({
          success: true,
          data: {
            ...cachedSuggestion,
            cached: true,
          },
          message: 'AI suggestion retrieved from cache',
        })
      }
    }

    // Fetch issue details
    const issue = await prisma.issue.findUnique({
      where: { id: issueId },
      include: {
        category: true,
        technologies: true,
        author: {
          select: { id: true, name: true },
        },
      },
    })

    if (!issue) {
      return res.status(404).json({
        success: false,
        error: 'Issue not found',
      })
    }

    // Check if user can access this issue (optional: implement privacy rules)
    // For now, allow all authenticated users to get suggestions

    // Find similar resolved issues
    const similarIssues = await dbUtils.getSimilarIssues(
      issueId,
      issue.title,
      issue.description,
      3 // Limit to 3 similar issues
    )

    // Prepare AI suggestion request
    const aiRequest: AISuggestionRequest = {
      issueTitle: issue.title,
      issueDescription: issue.description,
      errorMessage: issue.errorMessage || undefined,
      codeSnippet: issue.codeSnippet || undefined,
      stackTrace: issue.stackTrace || undefined,
      technologies: issue.technologies.map(tech => tech.name),
      severity: issue.severity,
      similarIssues: similarIssues.map(similar => ({
        ...similar,
        solutions: similar.solutions,
      })),
    }

    // Generate AI suggestion
    const startTime = Date.now()
    const suggestion = await aiSuggestionService.generateSuggestion(aiRequest)
    const processingTime = Date.now() - startTime

    // Estimate token count (rough approximation)
    const promptLength = JSON.stringify(aiRequest).length
    const responseLength = JSON.stringify(suggestion).length
    const estimatedTokens = Math.ceil((promptLength + responseLength) / 4) // Rough estimate: 4 chars per token

    // Save suggestion to database
    await aiSuggestionService.saveSuggestion(
      issueId,
      aiRequest,
      suggestion,
      processingTime,
      estimatedTokens
    )

    // Return the suggestion
    res.status(200).json({
      success: true,
      data: {
        ...suggestion,
        cached: false,
        processingTime,
        tokenCount: estimatedTokens,
      },
      message: 'AI suggestion generated successfully',
    })
  } catch (error) {
    console.error('Error generating AI suggestion:', error)

    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation error',
        message: error.errors[0].message,
      })
    }

    if (error.message.includes('OpenAI')) {
      return res.status(503).json({
        success: false,
        error: 'AI service unavailable',
        message: 'The AI suggestion service is temporarily unavailable. Please try again later.',
      })
    }

    res.status(500).json({
      success: false,
      error: 'Failed to generate AI suggestion',
      message: 'An unexpected error occurred while generating the suggestion.',
    })
  }
}