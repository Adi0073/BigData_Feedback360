## Feedback360 Annotation Algorithm (Pseudo-code)
FUNCTION process_feedback_event(raw_text, source_channel):
    INITIALIZE vader_analyzer
    
    // Step 1: Compute normalized polarity scores
    sentiment_scores = vader_analyzer.polarity_scores(raw_text)
    compound_score = sentiment_scores['compound']
    
    // Step 2: Threshold-based classification
    IF compound_score >= 0.05 THEN
        label = "Positive"
    ELSE IF compound_score <= -0.05 THEN
        label = "Negative"
    ELSE
        label = "Neutral"
        
    // Step 3: Package enriched event
    enriched_event = {
        timestamp: CURRENT_TIME(),
        channel: source_channel,
        text: raw_text,
        sentiment: label
    }
    
    // Step 4: Route to storage/visualization
    APPEND enriched_event TO unified_data_store
    UPDATE visualization_dashboard