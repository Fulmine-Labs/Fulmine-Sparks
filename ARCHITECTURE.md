# Fulmine-Spark Architecture

Lightning-powered AI image generation service with stateless, serverless-ready design.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                               │
│                   (Web/Mobile/CLI)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Service                          │
│              (Fulmine-Spark API Server)                     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Routes (routes.py)                  │  │
│  │  - POST /api/v1/invoice                             │  │
│  │  - GET /api/v1/image/{invoice_id}                   │  │
│  │  - POST /api/v1/moderation/check                    │  │
│  │  - POST /api/v1/payment/status                      │  │
│  │  - GET /api/v1/models                               │  │
│  │  - GET /api/v1/health                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│         ┌───────────────┼───────────────┐                   │
│         ▼               ▼               ▼                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ Moderation │ │  Payment   │ │   Image    │              │
│  │  Service   │ │  Service   │ │ Generation │              │
│  │            │ │            │ │  Service   │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
    ┌─────────┐    ┌──────────────┐   ┌──────────┐
    │ Keyword │    │  BTCPay      │   │Replicate │
    │ Filter  │    │  Server      │   │   API    │
    └─────────┘    └──────────────┘   └──────────┘
                        │                   │
                        ▼                   ▼
                   ┌──────────┐        ┌──────────┐
                   │Lightning │        │ Stable   │
                   │ Network  │        │Diffusion │
                   └──────────┘        │DALL-E   │
                                       │XL       │
                                       └──────────┘
```

## 📊 Data Flow

### 1. Invoice Creation Flow

```
Client Request
    │
    ▼
POST /api/v1/invoice
    │
    ├─ Validate Request (Pydantic)
    │
    ├─ Check Moderation
    │   └─ ModerationService.is_safe()
    │
    ├─ Get Model Cost
    │   └─ ImageGenerationService.get_cost()
    │
    ├─ Create Invoice
    │   └─ LightningPaymentService.create_invoice()
    │       └─ BTCPay API
    │
    └─ Return Invoice Response
        {
          "invoice_id": "abc123",
          "amount": 0.00001,
          "payment_request": "lnbc...",
          "status": "pending"
        }
```

### 2. Image Generation Flow

```
Client Request (After Payment)
    │
    ▼
GET /api/v1/image/{invoice_id}?prompt=...
    │
    ├─ Verify Payment
    │   └─ LightningPaymentService.is_payment_confirmed()
    │       └─ BTCPay API
    │
    ├─ Check Moderation
    │   └─ ModerationService.is_safe()
    │
    ├─ Generate Image
    │   └─ ImageGenerationService.generate_image()
    │       └─ Replicate API
    │           └─ Stable Diffusion / DALL-E
    │
    └─ Return Image Response
        {
          "status": "completed",
          "image_urls": ["https://..."],
          "processing_time": 45.2
        }
```

## 🔧 Component Details

### API Layer (routes.py)

**Responsibilities:**
- Request validation using Pydantic models
- Route handling and HTTP responses
- Error handling and logging
- CORS support

**Endpoints:**
- `POST /api/v1/invoice` - Create payment invoice
- `GET /api/v1/image/{invoice_id}` - Generate image
- `POST /api/v1/moderation/check` - Check content safety
- `POST /api/v1/payment/status` - Check payment status
- `GET /api/v1/models` - List available models
- `GET /api/v1/health` - Health check

### Moderation Service (moderation.py)

**Responsibilities:**
- Content safety filtering
- Keyword-based detection
- Configurable thresholds
- Safety scoring

**Features:**
- Detects explicit content
- Blocks violent content
- Filters hate speech
- Prevents illegal activity references
- Configurable threshold (0.0-1.0)

**Methods:**
- `score_prompt(prompt)` - Get safety score
- `is_safe(prompt, threshold)` - Check if safe
- `check_and_raise(prompt)` - Raise on unsafe

### Payment Service (lightning_payment.py)

**Responsibilities:**
- Lightning invoice creation
- Payment verification
- BTCPay Server integration
- Invoice status tracking

**Features:**
- Creates BOLT11 payment requests
- Verifies payment confirmation
- Tracks invoice status
- Handles payment webhooks

**Methods:**
- `create_invoice(amount, currency, description)` - Create invoice
- `get_invoice(invoice_id)` - Get invoice details
- `is_payment_confirmed(invoice_id)` - Check payment status

### Image Generation Service (image_generation.py)

**Responsibilities:**
- Replicate API integration
- Model management
- Image generation
- Cost calculation

**Supported Models:**
- Stable Diffusion v1.5 ($0.01)
- Stable Diffusion XL ($0.02)
- DALL-E 3 ($0.05)

**Methods:**
- `generate_image(prompt, model, ...)` - Generate image
- `get_model_info(model)` - Get model details
- `list_models()` - List available models
- `get_cost(model)` - Get model cost

### Configuration (config.py)

**Responsibilities:**
- Environment variable management
- Settings validation
- Default values
- Service configuration

**Settings:**
- Service host/port
- API keys (Replicate, BTCPay)
- Model pricing
- Moderation thresholds
- Image generation parameters

## 🏛️ Design Principles

### 1. Stateless Architecture
- No session state stored
- Each request is independent
- Horizontal scaling ready
- Serverless compatible

### 2. Separation of Concerns
- API layer handles HTTP
- Services handle business logic
- Config manages settings
- Models validate data

### 3. Security First
- API keys in environment variables
- Content moderation enabled
- Payment verification required
- No sensitive data logging

### 4. Error Handling
- Comprehensive exception handling
- Meaningful error messages
- Proper HTTP status codes
- Detailed logging

### 5. Scalability
- Async/await support
- Minimal dependencies
- Efficient resource usage
- Cloud-ready design

## 📦 Dependencies

```
fastapi==0.104.1          # Web framework
uvicorn==0.24.0           # ASGI server
pydantic==2.5.0           # Data validation
pydantic-settings==2.1.0  # Settings management
python-dotenv==1.0.0      # Environment variables
httpx==0.25.2             # Async HTTP client
replicate==0.20.0         # Replicate API client
requests==2.31.0          # HTTP client
pillow==10.1.0            # Image processing
```

## 🚀 Deployment Options

### 1. Docker Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "fulmine_spark.main"]
```

### 2. AWS Lambda
- Stateless design perfect for Lambda
- API Gateway integration
- Environment variables for config
- CloudWatch for logging

### 3. Google Cloud Run
- Container-based deployment
- Auto-scaling
- Pay-per-request pricing
- Environment variables support

### 4. Self-Hosted
- Docker Compose
- Kubernetes
- Traditional VPS
- On-premises servers

## 📈 Performance Characteristics

### Latency
- Invoice creation: ~500ms (BTCPay API call)
- Image generation: 30-60s (Replicate processing)
- Moderation check: <10ms (local keyword matching)
- Payment verification: ~500ms (BTCPay API call)

### Throughput
- Concurrent requests: Limited by Replicate API
- Replicate rate limit: 6 requests/minute (free tier)
- Horizontal scaling: Add more instances

### Resource Usage
- Memory: ~200MB per instance
- CPU: Minimal (mostly I/O bound)
- Storage: Stateless (no persistent storage)

## 🔐 Security Considerations

### API Security
- ✅ HTTPS ready
- ✅ CORS configured
- ✅ Input validation (Pydantic)
- ✅ Rate limiting ready

### Data Security
- ✅ API keys in environment variables
- ✅ No sensitive data in logs
- ✅ Payment verification required
- ✅ Content moderation enabled

### Infrastructure Security
- ✅ Stateless design
- ✅ No database required
- ✅ Minimal attack surface
- ✅ Cloud-native ready

## 📊 Monitoring & Logging

### Logging
- Service startup/shutdown
- Request/response logging
- Error logging with stack traces
- Performance metrics

### Health Checks
- Service health endpoint
- Component status reporting
- Configuration validation
- External service connectivity

### Metrics
- Request count
- Response times
- Error rates
- Image generation success rate

## 🔄 Future Enhancements

1. **Database Integration**
   - Store invoice history
   - Track user statistics
   - Payment analytics

2. **Advanced Moderation**
   - ML-based content filtering
   - Image analysis
   - User reputation system

3. **Additional Models**
   - More Stable Diffusion variants
   - Midjourney integration
   - Custom model support

4. **Payment Options**
   - On-chain Bitcoin payments
   - Stablecoin support
   - Fiat payment gateway

5. **Performance**
   - Image caching
   - Model optimization
   - CDN integration

## 📝 License

MIT License - See LICENSE file
