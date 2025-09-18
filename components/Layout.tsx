import { useState, useEffect, Fragment } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useSession, signOut } from 'next-auth/react'
import { Disclosure, Menu, Transition } from '@headlessui/react'
import {
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  ChartBarIcon,
  UserIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  CodeBracketIcon,
  SunIcon,
  MoonIcon,
} from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface LayoutProps {
  children: React.ReactNode
  title?: string
  description?: string
}

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  current?: boolean
}

export default function Layout({ children, title, description }: LayoutProps) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [darkMode, setDarkMode] = useState(false)

  // Initialize dark mode from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('darkMode')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    setDarkMode(saved ? JSON.parse(saved) : prefersDark)
  }, [])

  // Apply dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('darkMode', JSON.stringify(darkMode))
  }, [darkMode])

  const navigation: NavigationItem[] = [
    { name: 'Home', href: '/', icon: HomeIcon },
    { name: 'Browse Issues', href: '/issues', icon: MagnifyingGlassIcon },
    ...(session ? [
      { name: 'New Issue', href: '/issues/new', icon: PlusIcon },
      { name: 'Dashboard', href: '/dashboard', icon: ChartBarIcon },
    ] : []),
  ]

  const userNavigation = session ? [
    { name: 'Your Profile', href: '/profile' },
    { name: 'Settings', href: '/settings' },
  ] : []

  // Determine current page
  navigation.forEach(item => {
    item.current = router.pathname === item.href
  })

  const handleSignOut = async () => {
    await signOut({ callbackUrl: '/' })
  }

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Disclosure as="nav" className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        {({ open }) => (
          <>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex">
                  <div className="flex-shrink-0 flex items-center">
                    <Link href="/" className="flex items-center">
                      <CodeBracketIcon className="h-8 w-8 text-primary-600" />
                      <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">
                        Debug KB
                      </span>
                    </Link>
                  </div>
                  <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                    {navigation.map((item) => {
                      const Icon = item.icon
                      return (
                        <Link
                          key={item.name}
                          href={item.href}
                          className={clsx(
                            item.current
                              ? 'border-primary-500 text-gray-900 dark:text-white'
                              : 'border-transparent text-gray-500 dark:text-gray-300 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-200',
                            'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors'
                          )}
                        >
                          <Icon className="h-4 w-4 mr-2" />
                          {item.name}
                        </Link>
                      )
                    })}
                  </div>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:items-center space-x-4">
                  {/* Dark mode toggle */}
                  <button
                    onClick={toggleDarkMode}
                    className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-md"
                    title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                  >
                    {darkMode ? (
                      <SunIcon className="h-5 w-5" />
                    ) : (
                      <MoonIcon className="h-5 w-5" />
                    )}
                  </button>

                  {session ? (
                    <Menu as="div" className="relative">
                      <div>
                        <Menu.Button className="flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                          <span className="sr-only">Open user menu</span>
                          {session.user?.image ? (
                            <img
                              className="h-8 w-8 rounded-full"
                              src={session.user.image}
                              alt={session.user?.name || 'User'}
                            />
                          ) : (
                            <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
                              <UserIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                            </div>
                          )}
                        </Menu.Button>
                      </div>
                      <Transition
                        as={Fragment}
                        enter="transition ease-out duration-200"
                        enterFrom="transform opacity-0 scale-95"
                        enterTo="transform opacity-100 scale-100"
                        leave="transition ease-in duration-75"
                        leaveFrom="transform opacity-100 scale-100"
                        leaveTo="transform opacity-0 scale-95"
                      >
                        <Menu.Items className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                          <div className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-600">
                            <div className="font-medium">{session.user?.name}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">{session.user?.email}</div>
                          </div>
                          {userNavigation.map((item) => (
                            <Menu.Item key={item.name}>
                              {({ active }) => (
                                <Link
                                  href={item.href}
                                  className={clsx(
                                    active ? 'bg-gray-100 dark:bg-gray-700' : '',
                                    'block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                                  )}
                                >
                                  {item.name}
                                </Link>
                              )}
                            </Menu.Item>
                          ))}
                          <Menu.Item>
                            {({ active }) => (
                              <button
                                onClick={handleSignOut}
                                className={clsx(
                                  active ? 'bg-gray-100 dark:bg-gray-700' : '',
                                  'block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                                )}
                              >
                                <ArrowRightOnRectangleIcon className="h-4 w-4 inline mr-2" />
                                Sign out
                              </button>
                            )}
                          </Menu.Item>
                        </Menu.Items>
                      </Transition>
                    </Menu>
                  ) : (
                    <div className="flex items-center space-x-4">
                      <Link
                        href="/auth/signin"
                        className="text-gray-500 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 px-3 py-2 text-sm font-medium"
                      >
                        Sign In
                      </Link>
                      <Link
                        href="/auth/signup"
                        className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                      >
                        Sign Up
                      </Link>
                    </div>
                  )}
                </div>
                <div className="-mr-2 flex items-center sm:hidden">
                  {/* Dark mode toggle mobile */}
                  <button
                    onClick={toggleDarkMode}
                    className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-md mr-2"
                  >
                    {darkMode ? (
                      <SunIcon className="h-5 w-5" />
                    ) : (
                      <MoonIcon className="h-5 w-5" />
                    )}
                  </button>
                  
                  {/* Mobile menu button */}
                  <Disclosure.Button className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500">
                    <span className="sr-only">Open main menu</span>
                    {open ? (
                      <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
                    ) : (
                      <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
                    )}
                  </Disclosure.Button>
                </div>
              </div>
            </div>

            {/* Mobile menu */}
            <Disclosure.Panel className="sm:hidden">
              <div className="pt-2 pb-3 space-y-1">
                {navigation.map((item) => {
                  const Icon = item.icon
                  return (
                    <Disclosure.Button
                      key={item.name}
                      as={Link}
                      href={item.href}
                      className={clsx(
                        item.current
                          ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 text-primary-700 dark:text-primary-300'
                          : 'border-transparent text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-200',
                        'block pl-3 pr-4 py-2 border-l-4 text-base font-medium flex items-center'
                      )}
                    >
                      <Icon className="h-4 w-4 mr-3" />
                      {item.name}
                    </Disclosure.Button>
                  )
                })}
              </div>
              {session ? (
                <div className="pt-4 pb-3 border-t border-gray-200 dark:border-gray-600">
                  <div className="flex items-center px-4">
                    <div className="flex-shrink-0">
                      {session.user?.image ? (
                        <img
                          className="h-10 w-10 rounded-full"
                          src={session.user.image}
                          alt={session.user?.name || 'User'}
                        />
                      ) : (
                        <div className="h-10 w-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
                          <UserIcon className="h-6 w-6 text-gray-500 dark:text-gray-400" />
                        </div>
                      )}
                    </div>
                    <div className="ml-3">
                      <div className="text-base font-medium text-gray-800 dark:text-white">
                        {session.user?.name}
                      </div>
                      <div className="text-sm font-medium text-gray-500 dark:text-gray-300">
                        {session.user?.email}
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 space-y-1">
                    {userNavigation.map((item) => (
                      <Disclosure.Button
                        key={item.name}
                        as={Link}
                        href={item.href}
                        className="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        {item.name}
                      </Disclosure.Button>
                    ))}
                    <Disclosure.Button
                      as="button"
                      onClick={handleSignOut}
                      className="block w-full text-left px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Sign out
                    </Disclosure.Button>
                  </div>
                </div>
              ) : (
                <div className="pt-4 pb-3 border-t border-gray-200 dark:border-gray-600 space-y-1">
                  <Disclosure.Button
                    as={Link}
                    href="/auth/signin"
                    className="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Sign In
                  </Disclosure.Button>
                  <Disclosure.Button
                    as={Link}
                    href="/auth/signup"
                    className="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Sign Up
                  </Disclosure.Button>
                </div>
              )}
            </Disclosure.Panel>
          </>
        )}
      </Disclosure>

      {/* Page content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center">
                <CodeBracketIcon className="h-8 w-8 text-primary-600" />
                <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">
                  Debug KB
                </span>
              </div>
              <p className="mt-2 text-gray-600 dark:text-gray-300 max-w-md">
                A collaborative platform for developers to store, share, and discover 
                debugging solutions with AI-powered assistance.
              </p>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-400 dark:text-gray-300 tracking-wider uppercase">
                Platform
              </h3>
              <ul className="mt-4 space-y-2">
                <li>
                  <Link href="/issues" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                    Browse Issues
                  </Link>
                </li>
                <li>
                  <Link href="/categories" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                    Categories
                  </Link>
                </li>
                <li>
                  <Link href="/technologies" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                    Technologies
                  </Link>
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-400 dark:text-gray-300 tracking-wider uppercase">
                Support
              </h3>
              <ul className="mt-4 space-y-2">
                <li>
                  <Link href="/help" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                    Help Center
                  </Link>
                </li>
                <li>
                  <Link href="/contact" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                    Contact Us
                  </Link>
                </li>
                <li>
                  <Link href="/api-docs" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                    API Docs
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
            <p className="text-center text-gray-500 dark:text-gray-400 text-sm">
              © {new Date().getFullYear()} Code Debugging Knowledge Base. Built with Next.js and AI.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}