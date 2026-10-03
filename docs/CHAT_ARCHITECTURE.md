# Chat Request Flow

در تست RAG هر پیام به این مسیر می‌رود:

```text
Browser
  -> /api/playground/chat
      -> selected chat_model
      -> embedding(query)
      -> pgvector search
      -> prompt assembly
      -> chat completion(model=selected_model)
      -> save conversation
      -> response + sources + model
```

برای جلوگیری از درخواست‌های تکراری، رابط کاربری تا پایان درخواست دکمه ارسال را غیرفعال نگه می‌دارد.
