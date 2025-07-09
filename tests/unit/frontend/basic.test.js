/**
 * Basic test to verify Jest setup works
 */

describe('Basic Jest Setup', () => {
  test('should run basic tests', () => {
    expect(1 + 1).toBe(2);
  });
  
  test('should have DOM environment', () => {
    document.body.innerHTML = '<div id="test">Hello World</div>';
    const testElement = document.getElementById('test');
    expect(testElement).toBeTruthy();
    expect(testElement.textContent).toBe('Hello World');
  });
  
  test('should have access to jest mocks', () => {
    const mockFn = jest.fn();
    mockFn('test');
    expect(mockFn).toHaveBeenCalledWith('test');
  });
});