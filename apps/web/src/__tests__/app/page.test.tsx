import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

// Simple example component test for landing page structure
function MockLandingPage() {
  return (
    <div>
      <h1>Foundation Template</h1>
      <p>Get started with your next project</p>
    </div>
  )
}

describe('Landing Page Components', () => {
  it('renders main content structure', () => {
    render(<MockLandingPage />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Foundation Template')
  })
})
