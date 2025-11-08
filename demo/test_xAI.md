Here is a sample request command to use xAI API:
```
curl https://api.x.ai/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer API-KEY" \
    -d '{
      "messages": [
        {
          "role": "system",
          "content": "You are a test assistant."
        },
        {
          "role": "user",
          "content": "Testing. Just say hi and hello world and nothing else."
        }
      ],
      "model": "grok-4-latest",
      "stream": false,
      "temperature": 0
    }'
```

You will recieve a response like this:
```
{
  "id": "eae95cea-0e45-a31b-af52-ab2f32db7d56",
  "object": "chat.completion",
  "created": 1762581623,
  "model": "grok-4-0709",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "hi  \nhello world",
        "refusal": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 703,
    "completion_tokens": 4,
    "total_tokens": 957,
    "prompt_tokens_details": {
      "text_tokens": 703,
      "audio_tokens": 0,
      "image_tokens": 0,
      "cached_tokens": 679
    },
    "completion_tokens_details": {
      "reasoning_tokens": 250,
      "audio_tokens": 0,
      "accepted_prediction_tokens": 0,
      "rejected_prediction_tokens": 0
    },
    "num_sources_used": 0
  },
  "system_fingerprint": "fp_794271b43e"
}
```
