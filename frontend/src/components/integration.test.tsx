import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ArticleInput from './ArticleInput';

describe('ArticleInput Integration Tests', () => {
  it('integrates properly with real-world usage patterns', async () => {
    const user = userEvent.setup();
    const mockAnalyze = vi.fn().mockResolvedValue({
      id: '123',
      authenticityScore: 75,
      classification: 'reliable',
      sentenceAnalysis: [],
    });

    render(<ArticleInput onSubmit={mockAnalyze} isLoading={false} />);

    // Simulate a real user workflow
    const textarea = screen.getByLabelText(/article content/i);
    const urlInput = screen.getByLabelText(/source url/i);
    const titleInput = screen.getByLabelText(/article title/i);
    const submitButton = screen.getByRole('button', { name: /analyze content/i });

    // Fill out the form
    fireEvent.change(titleInput, { target: { value: 'Breaking News: Important Discovery' } });
    fireEvent.change(urlInput, { target: { value: 'https://news.example.com/article' } });
    fireEvent.change(textarea, { target: { value: 'Scientists have made an important discovery that could change everything. The research shows promising results in early trials.' } });

    // Verify all inputs are filled
    expect(titleInput).toHaveValue('Breaking News: Important Discovery');
    expect(urlInput).toHaveValue('https://news.example.com/article');
    expect(textarea).toHaveValue('Scientists have made an important discovery that could change everything. The research shows promising results in early trials.');

    // Verify submit button is enabled
    expect(submitButton).toBeEnabled();

    // Submit the form
    await user.click(submitButton);

    // Verify the handler was called with the content
    expect(mockAnalyze).toHaveBeenCalledWith('Scientists have made an important discovery that could change everything. The research shows promising results in early trials.');
  });

  it('handles edge cases gracefully', async () => {
    const user = userEvent.setup();
    const mockAnalyze = vi.fn().mockRejectedValue(new Error('Network error'));

    render(<ArticleInput onSubmit={mockAnalyze} isLoading={false} />);

    const textarea = screen.getByLabelText(/article content/i);
    const submitButton = screen.getByRole('button', { name: /analyze content/i });

    // Test with minimal valid content
    fireEvent.change(textarea, { target: { value: 'Test' } });
    await user.click(submitButton);

    expect(mockAnalyze).toHaveBeenCalledWith('Test');
  });

  it('works correctly with loading states', () => {
    render(<ArticleInput onSubmit={vi.fn()} isLoading={true} />);

    // All inputs should be disabled during loading
    expect(screen.getByLabelText(/article content/i)).toBeDisabled();
    expect(screen.getByLabelText(/article title/i)).toBeDisabled();
    expect(screen.getByLabelText(/source url/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /analyzing.../i })).toBeDisabled();
  });

  it('provides good user experience with immediate feedback', async () => {
    render(<ArticleInput onSubmit={vi.fn()} isLoading={false} />);

    // Test that character counter updates immediately
    const textarea = screen.getByLabelText(/article content/i);
    fireEvent.change(textarea, { target: { value: 'Hello world!' } });

    const characterCounter = document.querySelector('.character-counter span');
    expect(characterCounter?.textContent).toContain('12/50,000 characters');

    // Test that submit button becomes enabled immediately when content is added
    const submitButton = screen.getByRole('button', { name: /analyze content/i });
    expect(submitButton).toBeEnabled();
  });
});
