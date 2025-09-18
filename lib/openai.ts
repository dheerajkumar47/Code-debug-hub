import OpenAI from 'openai'
import { prisma } from './db'

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

// Types for AI suggestions
export interface AISuggestionRequest {
  issueTitle: string
  issueDescription: string
  errorMessage?: string
  codeSnippet?: string
  stackTrace?: string
  technologies: string[]
  severity: string
  similarIssues?: any[]
}

export interface AISuggestionResponse {
  suggestion: string
  confidence: number
  reasoning: string
  codeExample?: string
  steps: string[]
  additionalResources: string[]
}

// AI Suggestion Service
export class AISuggestionService {
  private model: string
  private maxTokens: number

  constructor() {
    this.model = process.env.OPENAI_MODEL || 'gpt-4'
    this.maxTokens = parseInt(process.env.OPENAI_MAX_TOKENS || '1000')
  }

  // Generate AI suggestion for an issue
  async generateSuggestion(request: AISuggestionRequest): Promise<AISuggestionResponse> {
    const startTime = Date.now()
    
    try {
      const prompt = this.buildPrompt(request)
      
      const completion = await openai.chat.completions.create({
        model: this.model,
        messages: [
          {
            role: 'system',
            content: this.getSystemPrompt(),
          },
          {
            role: 'user',
            content: prompt,
          },
        ],
        max_tokens: this.maxTokens,
        temperature: 0.3, // Lower temperature for more consistent technical advice
        top_p: 1,
        frequency_penalty: 0,
        presence_penalty: 0,
      })

      const processingTime = Date.now() - startTime
      const response = completion.choices[0].message.content

      if (!response) {
        throw new Error('Empty response from OpenAI')
      }

      // Parse the structured response
      const parsedResponse = this.parseAIResponse(response)
      
      // Calculate confidence based on response quality and similar issues
      const confidence = this.calculateConfidence(request, parsedResponse)

      return {
        ...parsedResponse,
        confidence,
      }
    } catch (error) {
      console.error('Error generating AI suggestion:', error)
      throw new Error('Failed to generate AI suggestion')
    }
  }

  // Save AI suggestion to database
  async saveSuggestion(
    issueId: string,
    request: AISuggestionRequest,
    response: AISuggestionResponse,
    processingTime: number,
    tokenCount: number
  ) {
    try {
      return await prisma.aISuggestion.create({
        data: {
          issueId,
          prompt: this.buildPrompt(request),
          response: JSON.stringify(response),
          model: this.model,
          confidence: response.confidence,
          tokenCount,
          processingTime,
        },
      })
    } catch (error) {
      console.error('Error saving AI suggestion:', error)
      throw error
    }
  }

  // Get cached suggestion if available
  async getCachedSuggestion(issueId: string) {
    try {
      const cached = await prisma.aISuggestion.findFirst({
        where: { issueId },
        orderBy: { createdAt: 'desc' },
      })

      if (cached && cached.response) {
        return JSON.parse(cached.response) as AISuggestionResponse
      }

      return null
    } catch (error) {
      console.error('Error fetching cached suggestion:', error)
      return null
    }
  }

  // Build the prompt for OpenAI
  private buildPrompt(request: AISuggestionRequest): string {
    let prompt = `I need help debugging the following issue:

**Title:** ${request.issueTitle}

**Description:** ${request.issueDescription}

**Technologies:** ${request.technologies.join(', ')}

**Severity:** ${request.severity}`

    if (request.errorMessage) {
      prompt += `\n\n**Error Message:**\n\`\`\`\n${request.errorMessage}\n\`\`\``
    }

    if (request.codeSnippet) {
      prompt += `\n\n**Code Snippet:**\n\`\`\`\n${request.codeSnippet}\n\`\`\``
    }

    if (request.stackTrace) {
      prompt += `\n\n**Stack Trace:**\n\`\`\`\n${request.stackTrace}\n\`\`\``
    }

    if (request.similarIssues && request.similarIssues.length > 0) {
      prompt += `\n\n**Similar Resolved Issues:**\n`
      request.similarIssues.forEach((issue, index) => {
        prompt += `${index + 1}. ${issue.title}\n`
        if (issue.solutions && issue.solutions.length > 0) {
          prompt += `   Solution: ${issue.solutions[0].title}\n`
        }
      })
    }

    prompt += `\n\nPlease provide a comprehensive debugging solution in the following JSON format:
{
  "suggestion": "Brief overview of the problem and suggested solution",
  "reasoning": "Detailed explanation of why this issue occurs",
  "codeExample": "Code example showing the fix (if applicable)",
  "steps": ["Step 1", "Step 2", "Step 3"],
  "additionalResources": ["URL 1", "URL 2"]
}`

    return prompt
  }

  // System prompt to guide AI behavior
  private getSystemPrompt(): string {
    return `You are an expert software debugging assistant with deep knowledge across multiple programming languages and technologies. Your role is to help developers solve coding issues by:

1. Analyzing error messages, code snippets, and stack traces
2. Providing clear, actionable solutions
3. Explaining the root cause of problems
4. Offering step-by-step debugging instructions
5. Suggesting best practices to prevent similar issues

Guidelines:
- Always respond with valid JSON format as requested
- Be specific and practical in your suggestions
- Include code examples when relevant
- Reference official documentation when possible
- Consider the technology stack and severity level
- Keep solutions concise but comprehensive
- If unsure, acknowledge limitations and suggest alternative approaches

Focus on providing accurate, tested solutions that developers can implement immediately.`
  }

  // Parse AI response into structured format
  private parseAIResponse(response: string): Omit<AISuggestionResponse, 'confidence'> {
    try {
      // Try to extract JSON from the response
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          suggestion: parsed.suggestion || 'No specific suggestion provided',
          reasoning: parsed.reasoning || 'No reasoning provided',
          codeExample: parsed.codeExample || undefined,
          steps: Array.isArray(parsed.steps) ? parsed.steps : [],
          additionalResources: Array.isArray(parsed.additionalResources) ? parsed.additionalResources : [],
        };
      }
      
      // Fallback: treat entire response as suggestion
      return {
        suggestion: response,
        reasoning: 'AI provided unstructured response',
        steps: [],
        additionalResources: [],
      };
    } catch (error) {
      console.error('Error parsing AI response:', error);
      return {
        suggestion: response,
        reasoning: 'Failed to parse structured response',
        steps: [],
        additionalResources: [],
      };
    }
  }

  // Calculate confidence score based on various factors
  private calculateConfidence(
    request: AISuggestionRequest,
    response: Omit<AISuggestionResponse, 'confidence'>
  ): number {
    let confidence = 0.5 // Base confidence

    // Increase confidence based on available information
    if (request.errorMessage) confidence += 0.2
    if (request.codeSnippet) confidence += 0.15
    if (request.stackTrace) confidence += 0.1
    if (request.similarIssues && request.similarIssues.length > 0) confidence += 0.1

    // Increase confidence based on response quality
    if (response.codeExample) confidence += 0.1
    if (response.steps.length > 0) confidence += 0.1
    if (response.reasoning.length > 100) confidence += 0.05

    // Adjust based on technology familiarity (simplified)
    const commonTechnologies = ['javascript', 'python', 'java', 'react', 'node.js']
    const hasCommonTech = request.technologies.some(tech => 
      commonTechnologies.some(common => tech.toLowerCase().includes(common))
    )
    if (hasCommonTech) confidence += 0.05

    // Ensure confidence is between 0 and 1
    return Math.min(Math.max(confidence, 0), 1)
  }

  // Generate embeddings for semantic search (optional advanced feature)
  async generateEmbedding(text: string): Promise<number[]> {
    try {
      const response = await openai.embeddings.create({
        model: 'text-embedding-ada-002',
        input: text,
      })

      return response.data[0].embedding
    } catch (error) {
      console.error('Error generating embedding:', error)
      throw error
    }
  }

  // Rate limiting check
  async checkRateLimit(userId?: string): Promise<boolean> {
    if (!userId) return true // Allow anonymous users with basic rate limiting

    try {
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
      const recentSuggestions = await prisma.aISuggestion.count({
        where: {
          createdAt: { gte: oneHourAgo },
          issue: { authorId: userId },
        },
      })

      // Allow 10 AI suggestions per hour per user
      return recentSuggestions < 10
    } catch (error) {
      console.error('Error checking rate limit:', error)
      return true // Allow on error
    }
  }
}

// Export singleton instance
export const aiSuggestionService = new AISuggestionService()