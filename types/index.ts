// Prisma generated types (will be imported from @prisma/client)
import type { 
  User, 
  Issue, 
  Solution, 
  Comment, 
  Category, 
  Technology, 
  AISuggestion,
  Severity,
  IssueStatus,
  Role 
} from '@prisma/client'

// Extended types with relations
export interface IssueWithRelations extends Issue {
  author: Pick<User, 'id' | 'name' | 'email' | 'image'>
  category: Category
  technologies: Technology[]
  solutions: SolutionWithAuthor[]
  comments: CommentWithAuthor[]
  aiSuggestions?: AISuggestion[]
  _count: {
    solutions: number
    comments: number
    aiSuggestions: number
  }
}

export interface SolutionWithAuthor extends Solution {
  author: Pick<User, 'id' | 'name' | 'email' | 'image'>
  issue?: Pick<Issue, 'id' | 'title'>
}

export interface CommentWithAuthor extends Comment {
  author: Pick<User, 'id' | 'name' | 'email' | 'image'>
}

export interface UserWithStats extends User {
  _count: {
    issues: number
    solutions: number
    comments: number
  }
  stats?: {
    totalUpvotes: number
    acceptedSolutions: number
    reputation: number
  }
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  pagination?: PaginationInfo
}

export interface PaginationInfo {
  page: number
  limit: number
  total: number
  totalPages: number
  hasMore: boolean
}

export interface SearchResponse<T> {
  items: T[]
  pagination: PaginationInfo
  filters?: SearchFilters
}

// Form and validation types
export interface CreateIssueData {
  title: string
  description: string
  errorMessage?: string
  codeSnippet?: string
  stackTrace?: string
  severity: Severity
  categoryId: string
  technologies: string[]
  environment?: string
}

export interface UpdateIssueData extends Partial<CreateIssueData> {
  status?: IssueStatus
}

export interface CreateSolutionData {
  title: string
  description: string
  codeSnippet?: string
  steps: string[]
  issueId: string
}

export interface CreateCommentData {
  content: string
  issueId: string
}

export interface CreateUserData {
  name?: string
  email: string
  password: string
}

// Search and filter types
export interface SearchFilters {
  query?: string
  categoryId?: string
  severity?: Severity
  status?: IssueStatus
  technologies?: string[]
  authorId?: string
  dateRange?: {
    start: Date
    end: Date
  }
  sortBy?: 'created' | 'updated' | 'upvotes' | 'views'
  sortOrder?: 'asc' | 'desc'
}

export interface SearchParams {
  q?: string
  category?: string
  severity?: string
  status?: string
  tech?: string[]
  author?: string
  page?: number
  limit?: number
  sort?: string
  order?: string
}

// AI Suggestion types
export interface AISuggestionRequest {
  issueTitle: string
  issueDescription: string
  errorMessage?: string
  codeSnippet?: string
  stackTrace?: string
  technologies: string[]
  severity: string
  similarIssues?: IssueWithRelations[]
}

export interface AISuggestionResponse {
  suggestion: string
  confidence: number
  reasoning: string
  codeExample?: string
  steps: string[]
  additionalResources: string[]
  processingTime?: number
  tokenCount?: number
}

// Component props types
export interface IssueCardProps {
  issue: IssueWithRelations
  showActions?: boolean
  compact?: boolean
  onUpdate?: (issue: IssueWithRelations) => void
  onDelete?: (issueId: string) => void
}

export interface SolutionCardProps {
  solution: SolutionWithAuthor
  showActions?: boolean
  onUpdate?: (solution: SolutionWithAuthor) => void
  onDelete?: (solutionId: string) => void
  onAccept?: (solutionId: string) => void
}

export interface SearchBarProps {
  onSearch: (filters: SearchFilters) => void
  initialFilters?: SearchFilters
  showAdvanced?: boolean
  placeholder?: string
}

export interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  showFirstLast?: boolean
  showPrevNext?: boolean
  maxVisiblePages?: number
}

// Dashboard and analytics types
export interface DashboardStats {
  totalIssues: number
  resolvedIssues: number
  pendingIssues: number
  totalSolutions: number
  acceptedSolutions: number
  totalUsers: number
  activeUsers: number
  aiSuggestionsGenerated: number
  mostCommonTechnologies: Array<{
    name: string
    count: number
  }>
  issuesByCategory: Array<{
    category: string
    count: number
  }>
  recentActivity: Array<{
    id: string
    type: 'issue' | 'solution' | 'comment'
    title: string
    author: string
    createdAt: Date
  }>
}

export interface UserActivity {
  issuesCreated: IssueWithRelations[]
  solutionsProvided: SolutionWithAuthor[]
  commentsPosted: CommentWithAuthor[]
  recentActivity: Array<{
    type: string
    item: any
    date: Date
  }>
}

// Notification types
export interface Notification {
  id: string
  userId: string
  type: 'issue_solved' | 'solution_accepted' | 'comment_added' | 'issue_updated'
  title: string
  message: string
  data?: Record<string, any>
  read: boolean
  createdAt: Date
}

// Settings and preferences
export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  emailNotifications: {
    issueSolved: boolean
    solutionAccepted: boolean
    newComments: boolean
    weeklyDigest: boolean
  }
  displayPreferences: {
    itemsPerPage: number
    defaultSort: string
    showCodePreview: boolean
  }
}

// File upload types
export interface UploadedFile {
  id: string
  filename: string
  originalName: string
  mimeType: string
  size: number
  url: string
  uploadedAt: Date
}

// Error handling types
export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
  statusCode: number
}

export interface FormError {
  field: string
  message: string
}

export interface ValidationError {
  errors: FormError[]
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

// Status and state types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
  lastFetched?: Date
}

// Route and navigation types
export interface BreadcrumbItem {
  label: string
  href?: string
  current?: boolean
}

export interface MenuItem {
  label: string
  href: string
  icon?: string
  active?: boolean
  children?: MenuItem[]
}

// Theme and styling types
export interface ThemeColors {
  primary: string
  secondary: string
  success: string
  warning: string
  error: string
  info: string
}

export interface ComponentVariants {
  size: 'sm' | 'md' | 'lg'
  variant: 'primary' | 'secondary' | 'outline' | 'ghost'
  state?: 'default' | 'hover' | 'active' | 'disabled'
}

// Export commonly used Prisma enums
export { Severity, IssueStatus, Role }

// Re-export Prisma types for convenience
export type {
  User,
  Issue,
  Solution,
  Comment,
  Category,
  Technology,
  AISuggestion,
}