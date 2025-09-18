import { NextApiRequest, NextApiResponse } from 'next'
import { authUtils } from '@/lib/auth'
import { z } from 'zod'
import { ApiResponse } from '@/types'

// Validation schema
const signupSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  name: z.string().min(2, 'Name must be at least 2 characters').optional(),
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

  try {
    // Validate request body
    const validatedData = signupSchema.parse(req.body)
    const { email, password, name } = validatedData

    // Additional password validation
    const passwordValidation = authUtils.isValidPassword(password)
    if (!passwordValidation.valid) {
      return res.status(400).json({
        success: false,
        error: passwordValidation.message,
      })
    }

    // Check if user already exists
    const userExists = await authUtils.userExists(email)
    if (userExists) {
      return res.status(400).json({
        success: false,
        error: 'User with this email already exists',
      })
    }

    // Create new user
    const user = await authUtils.createUser(email, password, name)

    // Remove password from response
    const { password: _, ...userWithoutPassword } = user

    res.status(201).json({
      success: true,
      data: userWithoutPassword,
      message: 'User created successfully',
    })
  } catch (error) {
    console.error('Signup error:', error)

    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation error',
        message: error.errors[0].message,
      })
    }

    res.status(500).json({
      success: false,
      error: 'Internal server error',
      message: 'Failed to create user',
    })
  }
}