import { useState, useEffect } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { useSession } from 'next-auth/react'
import { MagnifyingGlassIcon, PlusIcon, ChartBarIcon, CodeBracketIcon } from '@heroicons/react/24/outline'
import Layout from '@/components/Layout'
import SearchBar from '@/components/SearchBar'
import IssueList from '@/components/IssueList'
import { IssueWithRelations, SearchFilters } from '@/types'

interface HomeStats {
  totalIssues: number
  resolvedIssues: number
  totalSolutions: number
  activeUsers: number
  mostCommonTechnologies: Array<{
    name: string
    count: number
  }>
}

export default function Home() {
  const { data: session } = useSession()
  const [issues, setIssues] = useState<IssueWithRelations[]>([])
  const [stats, setStats] = useState<HomeStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({})

  // Fetch initial data
  useEffect(() => {
    Promise.all([
      fetchIssues(),
      fetchStats(),
    ]).finally(() => setLoading(false))
  }, [])

  const fetchIssues = async (filters: SearchFilters = {}) => {
    try {
      const params = new URLSearchParams()
      if (filters.query) params.append('q', filters.query)
      if (filters.categoryId) params.append('category', filters.categoryId)
      if (filters.severity) params.append('severity', filters.severity)
      if (filters.status) params.append('status', filters.status)
      if (filters.technologies) {
        filters.technologies.forEach(tech => params.append('tech', tech))
      }
      params.append('limit', '10') // Show 10 recent issues on homepage

      const response = await fetch(`/api/issues?${params}`)
      const data = await response.json()
      
      if (data.success) {
        setIssues(data.data)
      }
    } catch (error) {
      console.error('Error fetching issues:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats')
      const data = await response.json()
      
      if (data.success) {
        setStats(data.data)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleSearch = (filters: SearchFilters) => {
    setSearchFilters(filters)
    fetchIssues(filters)
  }

  const handleIssueUpdate = (updatedIssue: IssueWithRelations) => {
    setIssues(prev => prev.map(issue => 
      issue.id === updatedIssue.id ? updatedIssue : issue
    ))
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <Head>
        <title>Code Debugging Knowledge Base</title>
        <meta name="description" content="Store and retrieve debugging solutions with AI-powered suggestions" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <CodeBracketIcon className="h-12 w-12 text-primary-500 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              Code Debugging Knowledge Base
            </h1>
          </div>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
            Store and retrieve debugging solutions from past developer issues, powered by AI suggestions 
            to help you solve problems faster.
          </p>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            {session ? (
              <Link
                href="/issues/new"
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Report New Issue
              </Link>
            ) : (
              <Link
                href="/auth/signin"
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
              >
                Get Started
              </Link>
            )}
            
            <Link
              href="/issues"
              className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
            >
              <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
              Browse Issues
            </Link>
          </div>
        </div>

        {/* Search Section */}
        <div className="mb-12">
          <div className="max-w-4xl mx-auto">
            <SearchBar onSearch={handleSearch} placeholder="Search for debugging solutions..." />
          </div>
        </div>

        {/* Stats Section */}
        {stats && (
          <div className="mb-12">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <ChartBarIcon className="h-6 w-6 text-gray-400" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          Total Issues
                        </dt>
                        <dd className="text-lg font-medium text-gray-900 dark:text-white">
                          {stats.totalIssues.toLocaleString()}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-6 w-6 rounded-full bg-green-500"></div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          Resolved Issues
                        </dt>
                        <dd className="text-lg font-medium text-gray-900 dark:text-white">
                          {stats.resolvedIssues.toLocaleString()}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-6 w-6 rounded-full bg-blue-500"></div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          Total Solutions
                        </dt>
                        <dd className="text-lg font-medium text-gray-900 dark:text-white">
                          {stats.totalSolutions.toLocaleString()}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-6 w-6 rounded-full bg-purple-500"></div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          Active Users
                        </dt>
                        <dd className="text-lg font-medium text-gray-900 dark:text-white">
                          {stats.activeUsers.toLocaleString()}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recent Issues Section */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {searchFilters.query ? 'Search Results' : 'Recent Issues'}
            </h2>
            <Link
              href="/issues"
              className="text-primary-600 hover:text-primary-500 text-sm font-medium"
            >
              View all issues →
            </Link>
          </div>
          
          <IssueList
            issues={issues}
            loading={false}
            onUpdate={handleIssueUpdate}
            showPagination={false}
          />
        </div>

        {/* Popular Technologies */}
        {stats?.mostCommonTechnologies && stats.mostCommonTechnologies.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              Popular Technologies
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {stats.mostCommonTechnologies.slice(0, 10).map((tech) => (
                <Link
                  key={tech.name}
                  href={`/issues?tech=${encodeURIComponent(tech.name)}`}
                  className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="text-center">
                    <div className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                      {tech.name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {tech.count} issues
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Call to Action */}
        {!session && (
          <div className="bg-primary-50 dark:bg-primary-900 rounded-lg p-8 text-center">
            <h3 className="text-lg font-medium text-primary-900 dark:text-primary-100 mb-2">
              Ready to get started?
            </h3>
            <p className="text-primary-700 dark:text-primary-300 mb-4">
              Join our community of developers solving problems together with AI assistance.
            </p>
            <Link
              href="/auth/signin"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
            >
              Sign up now
            </Link>
          </div>
        )}
      </div>
    </Layout>
  )
}   