# Future Enhancements - Tax Assistant

## Usage Pattern Learning & Analytics

### Overview
Implement anonymous usage analytics to learn user patterns and improve the assistant's assumptions and UX.

### Implementation Plan

#### 1. Data Collection (Privacy-First)
**Location**: `services/api_gateway/analytics/`

**What to Track (Anonymous)**:
```typescript
interface UsageEvent {
  sessionId: string;           // Random UUID, not tied to user
  timestamp: string;
  eventType: 'input' | 'assumption_correct' | 'assumption_incorrect' | 'completion';
  
  // Input patterns
  inputText?: string;          // Hash or anonymize
  detectedPattern?: string;    // "income_only" | "family_complete" | "health_mentioned"
  
  // Assumption accuracy
  assumptionsMade?: string[];  // ["single_filing", "no_private_health", "aus_resident"]
  correctionsMade?: string[];  // Which assumptions were wrong
  
  // Completion metrics
  questionsAsked?: number;     // How many follow-ups needed
  timeToCompletion?: number;   // Seconds from start to result
}
```

#### 2. Pattern Analysis
**Location**: `packages/analytics/pattern_analyzer.py`

**Analysis Goals**:
- Most common input patterns
- Assumption accuracy rates by income bracket
- Common correction patterns
- Optimal quick-action button scenarios

**Features to Build**:
```python
class PatternAnalyzer:
    def analyze_input_patterns(self) -> Dict[str, float]:
        # Return frequency of input patterns
        
    def get_assumption_accuracy(self) -> Dict[str, float]:
        # Return accuracy rates for each assumption type
        
    def suggest_quick_actions(self) -> List[QuickAction]:
        # Suggest new quick action buttons based on usage
        
    def optimize_system_prompt(self) -> List[str]:
        # Suggest system prompt improvements
```

#### 3. Adaptive Features

**Smart Quick Actions**:
- Dynamically update quick action buttons based on usage patterns
- A/B test different button combinations
- Location: `apps/web/src/components/chat/SmartQuickActions.tsx`

**Context-Aware Assumptions**:
- Adjust default assumptions based on usage patterns
- Example: If 80% of users have private health, change default assumption
- Location: `services/agent/adaptive_assumptions.py`

**Personalized Onboarding**:
- Show different examples based on time of day, common patterns
- Location: `apps/web/src/components/chat/AdaptiveOnboarding.tsx`

#### 4. Implementation Steps

1. **Phase 1**: Basic anonymous event tracking
   - Add analytics middleware to API gateway
   - Track input patterns and completion rates
   - Store in lightweight DB (SQLite/PostgreSQL)

2. **Phase 2**: Pattern analysis and insights
   - Build analysis dashboard for insights
   - Generate weekly pattern reports
   - Identify optimization opportunities

3. **Phase 3**: Adaptive features
   - Dynamic quick actions based on usage
   - A/B testing framework
   - Automatic assumption optimization

#### 5. Privacy & Ethics
- **Zero PII**: Never store personal income amounts or identifying info
- **Opt-out**: Users can disable analytics entirely
- **Transparency**: Clear disclosure of what's tracked
- **Data retention**: Auto-delete data after 90 days

#### 6. Technical Implementation

**Database Schema**:
```sql
CREATE TABLE usage_events (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_session ON usage_events(session_id);
CREATE INDEX idx_events_type ON usage_events(event_type);
CREATE INDEX idx_events_timestamp ON usage_events(timestamp);
```

**Environment Variables**:
```env
ANALYTICS_ENABLED=true
ANALYTICS_RETENTION_DAYS=90
ANALYTICS_DB_URL=postgresql://...
```

### Benefits
- **Reduced friction**: Learn optimal assumption defaults
- **Better UX**: Data-driven quick actions and examples
- **Continuous improvement**: Automatic system optimization
- **User satisfaction**: Fewer questions, faster results

### Estimated Timeline
- **Phase 1**: 1-2 weeks
- **Phase 2**: 2-3 weeks  
- **Phase 3**: 3-4 weeks

### Files to Create
```
services/api_gateway/analytics/
├── __init__.py
├── events.py              # Event tracking middleware
├── models.py              # Database models
└── analyzer.py            # Pattern analysis

packages/analytics/
├── __init__.py
├── pattern_analyzer.py    # Core analysis logic
└── insights.py            # Generate insights/reports

apps/web/src/analytics/
├── tracker.ts             # Client-side event tracking
└── types.ts               # TypeScript definitions
```

---

**Note**: This feature should be implemented after the core tax calculation functionality is stable and user feedback validates the assumption-based approach.