describe('Starter E2E Test', () => {
  beforeAll(async () => {
    await device.launchApp()
  })

  beforeEach(async () => {
    await device.reloadReactNative()
  })

  it('should show app content on launch', async () => {
    // Verify the app launches successfully
    // This is a basic smoke test to ensure Detox is configured correctly
    await expect(element(by.text('Sign In'))).toBeVisible()
  })

  it('should navigate to tabs after auth', async () => {
    // This test demonstrates navigation testing
    // In a real scenario, you would test the full authentication flow
    // For now, this serves as a placeholder showing the pattern
    await expect(element(by.text('Sign In'))).toExist()
  })
})
