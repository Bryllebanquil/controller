# Screenshot Debugging Guide

## Overview
This guide explains how to use the screenshot debugger, accuracy monitoring, and logs to diagnose capture issues and performance.

## Enable Debug Mode
### Frontend
1. Open the browser console.
2. Run `localStorage.setItem('screenshot_debug', 'true')`.
3. Refresh the page.

Debugger breakpoints will trigger on capture start, response handling, and error paths in development builds.

### Agent
Set the environment variable `SCREENSHOT_DEBUG=1` before starting the agent process. The handler will break into the debugger at key points in development usage.

## Common Signals to Check
### Accuracy
- Accuracy is calculated per capture based on duration, size, and retries.
- The average accuracy is shown beneath the capture panel.

### Duration
- Long durations lower accuracy and may indicate network latency or capture delays.
- Compare durations between successful and failed captures.

### Image Size
- Very small base64 sizes indicate incomplete or invalid captures.
- If size repeatedly falls below the baseline, check agent display availability or permissions.

## Troubleshooting Steps
1. Confirm socket connectivity and agent selection.
2. Trigger a capture and watch the screenshot log entries.
3. Inspect accuracy drops alongside duration and size.
4. If errors occur, read the error message in the log and use debugger breaks to inspect state.
5. Retry the capture and compare metrics to spot recurring issues.

## Disable Debug Mode
- Frontend: `localStorage.removeItem('screenshot_debug')` and refresh.
- Agent: unset `SCREENSHOT_DEBUG`.
