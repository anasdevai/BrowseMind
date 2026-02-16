---
name: react
description: Build modern React applications with best practices. Use when creating React components, hooks, state management, or when user mentions React, JSX, components, useState, useEffect, context, or frontend development.
---

# React Framework Skill

When building React applications, follow these patterns and best practices:

## 1. Project Structure

```
react-app/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   └── Input.tsx
│   │   └── features/
│   │       └── UserProfile.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useFetch.ts
│   ├── contexts/
│   │   └── AuthContext.tsx
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── index.ts
│   ├── utils/
│   │   └── helpers.ts
│   ├── App.tsx
│   └── index.tsx
├── package.json
└── tsconfig.json
```

## 2. Functional Components with TypeScript

```typescript
// components/UserProfile.tsx
import React, { FC } from 'react'

interface UserProfileProps {
  userId: string
  name: string
  email: string
  avatar?: string
  onEdit?: () => void
  className?: string
}

export const UserProfile: FC<UserProfileProps> = ({
  userId,
  name,
  email,
  avatar,
  onEdit,
  className = ''
}) => {
  return (
    <div className={`user-profile ${className}`}>
      {avatar && <img src={avatar} alt={name} />}
      <h2>{name}</h2>
      <p>{email}</p>
      {onEdit && (
        <button onClick={onEdit}>Edit Profile</button>
      )}
    </div>
  )
}

// Default props alternative
UserProfile.defaultProps = {
  avatar: '/default-avatar.png'
}
```

## 3. State Management with useState

```typescript
import { useState } from 'react'

function Counter() {
  const [count, setCount] = useState(0)
  const [isActive, setIsActive] = useState(false)

  // Functional updates for complex state
  const increment = () => {
    setCount(prev => prev + 1)
  }

  // Multiple state updates
  const reset = () => {
    setCount(0)
    setIsActive(false)
  }

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={increment}>+1</button>
      <button onClick={reset}>Reset</button>
    </div>
  )
}

// Complex state with objects
interface User {
  name: string
  email: string
  preferences: {
    theme: string
    notifications: boolean
  }
}

function UserSettings() {
  const [user, setUser] = useState<User>({
    name: '',
    email: '',
    preferences: {
      theme: 'light',
      notifications: true
    }
  })

  // Update nested state
  const updateTheme = (theme: string) => {
    setUser(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        theme
      }
    }))
  }

  return (
    <div>
      <input
        value={user.name}
        onChange={(e) => setUser(prev => ({ ...prev, name: e.target.value }))}
      />
      <select value={user.preferences.theme} onChange={(e) => updateTheme(e.target.value)}>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </div>
  )
}
```

## 4. Effects with useEffect

```typescript
import { useState, useEffect } from 'react'

function DataFetcher({ userId }: { userId: string }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    // Reset state on userId change
    setLoading(true)
    setError(null)

    // Create abort controller for cleanup
    const controller = new AbortController()

    async function fetchData() {
      try {
        const response = await fetch(`/api/users/${userId}`, {
          signal: controller.signal
        })
        const json = await response.json()
        setData(json)
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err)
        }
      } finally {
        setLoading(false)
      }
    }

    fetchData()

    // Cleanup function
    return () => {
      controller.abort()
    }
  }, [userId]) // Dependency array

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>
  return <div>{JSON.stringify(data)}</div>
}

// Event listeners
function WindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  })

  useEffect(() => {
    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight
      })
    }

    window.addEventListener('resize', handleResize)
    
    // Cleanup
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return <div>{size.width} x {size.height}</div>
}
```

## 5. Custom Hooks

```typescript
// hooks/useFetch.ts
import { useState, useEffect } from 'react'

interface FetchState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

export function useFetch<T>(url: string): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    error: null
  })

  useEffect(() => {
    const controller = new AbortController()

    async function fetchData() {
      try {
        const response = await fetch(url, { signal: controller.signal })
        if (!response.ok) throw new Error('Network response was not ok')
        const data = await response.json()
        setState({ data, loading: false, error: null })
      } catch (error) {
        if (error.name !== 'AbortError') {
          setState({ data: null, loading: false, error })
        }
      }
    }

    fetchData()
    return () => controller.abort()
  }, [url])

  return state
}

// hooks/useLocalStorage.ts
import { useState, useEffect } from 'react'

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.error(error)
      return initialValue
    }
  })

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.error(error)
    }
  }

  return [storedValue, setValue] as const
}

// hooks/useDebounce.ts
import { useState, useEffect } from 'react'

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// Usage
function SearchComponent() {
  const [searchTerm, setSearchTerm] = useState('')
  const debouncedSearchTerm = useDebounce(searchTerm, 500)

  useEffect(() => {
    if (debouncedSearchTerm) {
      // Perform search
      console.log('Searching for:', debouncedSearchTerm)
    }
  }, [debouncedSearchTerm])

  return (
    <input
      type="text"
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      placeholder="Search..."
    />
  )
}
```

## 6. Context API for Global State

```typescript
// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: string
  name: string
  email: string
}

interface AuthContextType {
  user: User | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/me')
        if (response.ok) {
          const userData = await response.json()
          setUser(userData)
        }
      } catch (error) {
        console.error('Auth check failed:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })

    if (!response.ok) throw new Error('Login failed')

    const userData = await response.json()
    setUser(userData)
  }

  const logout = () => {
    setUser(null)
    // Clear session
    fetch('/api/auth/logout', { method: 'POST' })
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook for using auth context
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

// Usage in components
function LoginForm() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
    } catch (error) {
      console.error('Login error:', error)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Login</button>
    </form>
  )
}
```

## 7. Form Handling

```typescript
import { useState, FormEvent, ChangeEvent } from 'react'

interface FormData {
  name: string
  email: string
  message: string
}

function ContactForm() {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    message: ''
  })
  const [errors, setErrors] = useState<Partial<FormData>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    
    // Clear error when user types
    if (errors[name as keyof FormData]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }

  const validate = (): boolean => {
    const newErrors: Partial<FormData> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid'
    }

    if (!formData.message.trim()) {
      newErrors.message = 'Message is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    setIsSubmitting(true)

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      if (!response.ok) throw new Error('Submission failed')

      // Reset form
      setFormData({ name: '', email: '', message: '' })
      alert('Form submitted successfully!')
    } catch (error) {
      alert('Error submitting form')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <input
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="Name"
        />
        {errors.name && <span className="error">{errors.name}</span>}
      </div>

      <div>
        <input
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Email"
        />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>

      <div>
        <textarea
          name="message"
          value={formData.message}
          onChange={handleChange}
          placeholder="Message"
        />
        {errors.message && <span className="error">{errors.message}</span>}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  )
}
```

## 8. Lists and Keys

```typescript
interface Todo {
  id: string
  text: string
  completed: boolean
}

function TodoList() {
  const [todos, setTodos] = useState<Todo[]>([
    { id: '1', text: 'Learn React', completed: false },
    { id: '2', text: 'Build app', completed: false }
  ])

  const toggleTodo = (id: string) => {
    setTodos(prev =>
      prev.map(todo =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    )
  }

  const deleteTodo = (id: string) => {
    setTodos(prev => prev.filter(todo => todo.id !== id))
  }

  const addTodo = (text: string) => {
    const newTodo: Todo = {
      id: Date.now().toString(),
      text,
      completed: false
    }
    setTodos(prev => [...prev, newTodo])
  }

  return (
    <div>
      <ul>
        {todos.map(todo => (
          <li key={todo.id}>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => toggleTodo(todo.id)}
            />
            <span
              style={{
                textDecoration: todo.completed ? 'line-through' : 'none'
              }}
            >
              {todo.text}
            </span>
            <button onClick={() => deleteTodo(todo.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

## 9. Conditional Rendering

```typescript
function UserDashboard({ user }: { user: User | null }) {
  // Early return pattern
  if (!user) {
    return <LoginPrompt />
  }

  // Ternary operator
  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      {user.isPremium ? (
        <PremiumFeatures />
      ) : (
        <UpgradePrompt />
      )}
    </div>
  )
}

// Logical AND operator
function Notification({ message }: { message?: string }) {
  return (
    <div>
      {message && (
        <div className="notification">{message}</div>
      )}
    </div>
  )
}

// Switch-like rendering with objects
function StatusBadge({ status }: { status: string }) {
  const badges = {
    pending: <span className="badge-yellow">Pending</span>,
    approved: <span className="badge-green">Approved</span>,
    rejected: <span className="badge-red">Rejected</span>
  }

  return badges[status] || <span>Unknown</span>
}
```

## 10. Performance Optimization

```typescript
import { memo, useMemo, useCallback } from 'react'

// Memoize expensive components
const ExpensiveComponent = memo(({ data }: { data: any[] }) => {
  console.log('ExpensiveComponent rendered')
  return (
    <div>
      {data.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  )
})

// useMemo for expensive calculations
function DataProcessor({ items }: { items: number[] }) {
  const processedData = useMemo(() => {
    console.log('Processing data...')
    return items
      .filter(n => n > 0)
      .map(n => n * 2)
      .reduce((sum, n) => sum + n, 0)
  }, [items])

  return <div>Sum: {processedData}</div>
}

// useCallback for stable function references
function ParentComponent() {
  const [count, setCount] = useState(0)
  const [other, setOther] = useState(0)

  // Without useCallback, this creates new function on every render
  const handleClick = useCallback(() => {
    setCount(c => c + 1)
  }, [])

  return (
    <div>
      <ChildComponent onClick={handleClick} />
      <button onClick={() => setOther(o => o + 1)}>
        Other: {other}
      </button>
    </div>
  )
}

const ChildComponent = memo(({ onClick }: { onClick: () => void }) => {
  console.log('ChildComponent rendered')
  return <button onClick={onClick}>Increment</button>
})
```

## 11. Error Boundaries

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    // Log to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div>
            <h1>Something went wrong</h1>
            <p>{this.state.error?.message}</p>
          </div>
        )
      )
    }

    return this.props.children
  }
}

// Usage
function App() {
  return (
    <ErrorBoundary>
      <MyComponent />
    </ErrorBoundary>
  )
}
```

## 12. Portals

```typescript
import { createPortal } from 'react-dom'
import { useState } from 'react'

function Modal({ isOpen, onClose, children }) {
  if (!isOpen) return null

  return createPortal(
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {children}
        <button onClick={onClose}>Close</button>
      </div>
    </div>,
    document.body
  )
}

// Usage
function App() {
  const [isModalOpen, setIsModalOpen] = useState(false)

  return (
    <div>
      <button onClick={() => setIsModalOpen(true)}>Open Modal</button>
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)}>
        <h2>Modal Content</h2>
        <p>This renders outside the root div!</p>
      </Modal>
    </div>
  )
}
```

## Best Practices

1. **Use Functional Components**: Prefer function components over class components
2. **TypeScript**: Use TypeScript for type safety
3. **Component Composition**: Break down complex components into smaller ones
4. **Custom Hooks**: Extract reusable logic into custom hooks
5. **Avoid Prop Drilling**: Use Context API or state management libraries
6. **Keys in Lists**: Always provide unique keys for list items
7. **Controlled Components**: Prefer controlled inputs over uncontrolled
8. **Error Handling**: Use Error Boundaries and try-catch blocks
9. **Cleanup Effects**: Always cleanup in useEffect return function
10. **Performance**: Use memo, useMemo, useCallback judiciously

## Common Patterns

### Compound Components
```typescript
function Tabs({ children }) {
  const [activeTab, setActiveTab] = useState(0)

  return (
    <div className="tabs">
      {React.Children.map(children, (child, index) =>
        React.cloneElement(child, {
          isActive: index === activeTab,
          onClick: () => setActiveTab(index)
        })
      )}
    </div>
  )
}

function Tab({ label, isActive, onClick, children }) {
  return (
    <div>
      <button onClick={onClick} className={isActive ? 'active' : ''}>
        {label}
      </button>
      {isActive && <div>{children}</div>}
    </div>
  )
}

// Usage
<Tabs>
  <Tab label="Tab 1">Content 1</Tab>
  <Tab label="Tab 2">Content 2</Tab>
</Tabs>
```

### Render Props
```typescript
function MouseTracker({ render }) {
  const [position, setPosition] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handleMove = (e) => {
      setPosition({ x: e.clientX, y: e.clientY })
    }
    window.addEventListener('mousemove', handleMove)
    return () => window.removeEventListener('mousemove', handleMove)
  }, [])

  return render(position)
}

// Usage
<MouseTracker render={({ x, y }) => (
  <p>Mouse is at {x}, {y}</p>
)} />
```

Remember: React is all about components and data flow. Keep components small, focused, and reusable!
