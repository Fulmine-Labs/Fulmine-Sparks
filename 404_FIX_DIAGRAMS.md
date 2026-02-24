# 404 Status Endpoint Fix - Visual Diagrams

## 🔴 The Problem: Lambda Statelessness

### Current Architecture (Broken)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                           │
│                                                                 │
│  1. POST /api/v1/services/image/generate                       │
│     └─> "Generate a sunset image"                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAMBDA INVOCATION #1 (Process A)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Memory Space (Invocation #1)                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ IMAGE_CACHE = {                                         │   │
│  │   "b4db0ffe...": {                                      │   │
│  │     image_base64: "iVBORw0KGgo...",                     │   │
│  │     status: "pending",                                  │   │
│  │     expires_at: 1708617615                              │   │
│  │   }                                                     │   │
│  │ }                                                       │   │
│  │                                                         │   │
│  │ ✅ Image stored in memory                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Return: {                                                      │
│    status: "payment_required",                                  │
│    invoice: {...},                                              │
│    payment_hash: "b4db0ffe..."                                  │
│  }                                                              │
│                                                                 │
│  Lambda execution ends ❌ Memory is freed                       │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                           │
│                                                                 │
│  2. GET /api/v1/services/image/status/b4db0ffe...             │
│     └─> "Check if payment received"                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAMBDA INVOCATION #2 (Process B)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Memory Space (Invocation #2)                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ IMAGE_CACHE = {} ❌ EMPTY!                              │   │
│  │                                                         │   │
│  │ (Different process, fresh memory)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  get_image_status("b4db0ffe..."):                              │
│    if "b4db0ffe..." in IMAGE_CACHE:  ❌ FALSE                  │
│      return status                                              │
│    return None  ❌ Returns None                                 │
│                                                                 │
│  Return: 404 Not Found ❌                                       │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                           │
│                                                                 │
│  ❌ Error: 404 Client Error: Not Found                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ The Solution: Persistent Storage

### Fixed Architecture (Working)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                           │
│                                                                 │
│  1. POST /api/v1/services/image/generate                       │
│     └─> "Generate a sunset image"                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAMBDA INVOCATION #1 (Process A)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Memory Space (Invocation #1)                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ IMAGE_CACHE = {                                         │   │
│  │   "b4db0ffe...": {image_data}                           │   │
│  │ }                                                       │   │
│  │ ✅ Stored in memory                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DynamoDB (Persistent)                                   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Table: fulmine-sparks-images                            │   │
│  │                                                         │   │
│  │ Item: {                                                 │   │
│  │   payment_hash: "b4db0ffe...",                          │   │
│  │   image_base64: "iVBORw0KGgo...",                       │   │
│  │   status: "pending",                                    │   │
│  │   expires_at: 1708617615,                               │   │
│  │   ttl: 1708617615                                       │   │
│  │ }                                                       │   │
│  │ ✅ Stored in DynamoDB                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Lambda execution ends ✅ Data persists in DynamoDB             │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                           │
│                                                                 │
│  2. GET /api/v1/services/image/status/b4db0ffe...             │
│     └─> "Check if payment received"                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAMBDA INVOCATION #2 (Process B)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Memory Space (Invocation #2)                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ IMAGE_CACHE = {} (empty)                                │   │
│  │                                                         │   │
│  │ (Different process, fresh memory)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  get_image_status("b4db0ffe..."):                              │
│    if "b4db0ffe..." in IMAGE_CACHE:  ❌ FALSE                  │
│      return status                                              │
│                                                                 │
│    ✅ Check DynamoDB:                                          │
│    response = images_table.get_item(                           │
│      Key={'payment_hash': 'b4db0ffe...'}                       │
│    )                                                           │
│    if 'Item' in response:  ✅ TRUE                             │
│      return response['Item']['status']  ✅ "pending"           │
│                                                                 │
│  Return: {                                                      │
│    status: "pending",                                           │
│    payment_hash: "b4db0ffe..."                                  │
│  } ✅                                                           │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                           │
│                                                                 │
│  ✅ Status: pending                                             │
│  ✅ Payment Hash: b4db0ffe...                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Flow with DynamoDB

```
┌──────────────────────────────────────────────────────────────────────┐
│                         COMPLETE WORKFLOW                            │
└──────────────────────────────────────────────────────────────────────┘

STEP 1: Generate Image
┌──────────────────────────────────────────────────────────────────────┐
│ Client: POST /api/v1/services/image/generate                        │
│         {prompt: "A beautiful sunset"}                              │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Lambda Invocation #1                                                 │
├──────────────────────────────────────────────────────────────────────┤
│ 1. Call Replicate API (10-15 seconds)                               │
│ 2. Get image URL                                                    │
│ 3. Convert to base64                                                │
│ 4. Create Lightning invoice                                         │
│ 5. store_image(payment_hash, image_base64):                         │
│    ├─ IMAGE_CACHE[payment_hash] = {...}  ✅ Memory                 │
│    └─ images_table.put_item({...})       ✅ DynamoDB               │
│ 6. Return invoice                                                   │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Client: Receives invoice with payment_hash                          │
│ Displays QR code and waits for payment                              │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: Poll Status (Every 1 second)                                │
│ Client: GET /api/v1/services/image/status/{payment_hash}           │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Lambda Invocation #2 (NEW PROCESS)                                   │
├──────────────────────────────────────────────────────────────────────┤
│ get_image_status(payment_hash):                                     │
│ 1. Check IMAGE_CACHE (empty)                                        │
│ 2. Check DynamoDB:                                                  │
│    response = images_table.get_item(                                │
│      Key={'payment_hash': payment_hash}                             │
│    )                                                                │
│ 3. Return status from DynamoDB ✅                                   │
│                                                                     │
│ Also check Alby for payment:                                        │
│ 4. If payment confirmed:                                            │
│    mark_image_available(payment_hash):                              │
│    ├─ IMAGE_CACHE[payment_hash]['status'] = 'available'            │
│    └─ images_table.update_item(status='available')                 │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Client: Receives status                                             │
│ If status == "pending": Keep polling                                │
│ If status == "available": Proceed to retrieve                       │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: Retrieve Image (After Payment)                              │
│ Client: GET /api/v1/services/image/retrieve/{payment_hash}         │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Lambda Invocation #3 (NEW PROCESS)                                   │
├──────────────────────────────────────────────────────────────────────┤
│ retrieve_image(payment_hash):                                       │
│ 1. get_image_status(payment_hash):                                  │
│    ├─ Check IMAGE_CACHE (empty)                                    │
│    └─ Check DynamoDB ✅ Found!                                     │
│ 2. get_cached_image(payment_hash):                                  │
│    ├─ Check IMAGE_CACHE (empty)                                    │
│    └─ Check DynamoDB ✅ Get image_base64                           │
│ 3. delete_cached_image(payment_hash):                               │
│    ├─ Delete from IMAGE_CACHE                                      │
│    └─ Delete from DynamoDB                                         │
│ 4. Return image ✅                                                  │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Client: Receives image                                              │
│ Displays image to user ✅                                           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      IMAGE LIFECYCLE                                │
└─────────────────────────────────────────────────────────────────────┘

Time    Memory Cache          DynamoDB              Status
────────────────────────────────────────────────────────────────────
0s      ✅ Created            ✅ Created            pending
        (fast access)         (persistent)

5s      ✅ Available          ✅ Available          available
        (payment confirmed)   (payment confirmed)   (after payment)

10s     ✅ Available          ✅ Available          available
        (ready to retrieve)   (ready to retrieve)

15s     ❌ Expired            ❌ Expired            expired
        (auto-deleted)        (TTL triggered)       (auto-deleted)


┌─────────────────────────────────────────────────────────────────────┐
│                    CACHE LOOKUP STRATEGY                            │
└─────────────────────────────────────────────────────────────────────┘

get_image_status(payment_hash):
│
├─ Check Memory Cache
│  ├─ Found? ✅ Return status
│  └─ Not found? Continue...
│
├─ Check DynamoDB
│  ├─ Found? ✅ Return status
│  └─ Not found? Continue...
│
└─ Return None (404)


get_cached_image(payment_hash):
│
├─ Check Memory Cache
│  ├─ Found & not expired? ✅ Return image
│  └─ Not found? Continue...
│
├─ Check DynamoDB
│  ├─ Found & not expired? 
│  │  ├─ Restore to memory cache (for speed)
│  │  └─ ✅ Return image
│  └─ Not found? Continue...
│
└─ Return None (404)
```

---

## 🔄 State Transitions

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IMAGE STATE MACHINE                              │
└─────────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   CREATED    │
                    │  (pending)   │
                    └──────┬───────┘
                           │
                    store_image()
                           │
                    ┌──────▼───────┐
                    │   PENDING    │
                    │  (waiting)   │
                    └──────┬───────┘
                           │
                  (payment received)
                           │
            mark_image_available()
                           │
                    ┌──────▼───────┐
                    │  AVAILABLE   │
                    │  (ready)     │
                    └──────┬───────┘
                           │
                  retrieve_image()
                           │
            delete_cached_image()
                           │
                    ┌──────▼───────┐
                    │   DELETED    │
                    │  (cleaned)   │
                    └──────────────┘


OR (if timeout):

                    ┌──────────────┐
                    │   PENDING    │
                    │  (waiting)   │
                    └──────┬───────┘
                           │
                  (15 seconds elapsed)
                           │
                    ┌──────▼───────┐
                    │   EXPIRED    │
                    │  (TTL)       │
                    └──────┬───────┘
                           │
                  (auto-deleted by DynamoDB)
                           │
                    ┌──────▼───────┐
                    │   DELETED    │
                    │  (cleaned)   │
                    └──────────────┘
```

---

## 🗄️ DynamoDB Table Schema

```
┌─────────────────────────────────────────────────────────────────────┐
│              fulmine-sparks-images (DynamoDB Table)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Primary Key: payment_hash (String)                                │
│  TTL Attribute: ttl (Number)                                       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Item Example:                                               │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ {                                                           │   │
│  │   "payment_hash": "b4db0ffe4895fe18...",                   │   │
│  │   "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",      │   │
│  │   "status": "pending",                                      │   │
│  │   "created_at": 1708617600,                                │   │
│  │   "expires_at": 1708617615,                                │   │
│  │   "ttl": 1708617615,                                        │   │
│  │   "polling_started": false,                                │   │
│  │   "polling_expires_at": 1708617605                          │   │
│  │ }                                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Billing Mode: PAY_PER_REQUEST (on-demand)                         │
│  TTL: Enabled (auto-delete after expires_at)                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔀 Comparison: Before vs After

```
┌──────────────────────────────────────────────────────────────────────┐
│                    BEFORE (Broken)                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Invocation 1: Generate image                                       │
│  ├─ Store in IMAGE_CACHE ✅                                         │
│  └─ Lambda ends (memory freed)                                      │
│                                                                      │
│  Invocation 2: Poll status                                          │
│  ├─ Check IMAGE_CACHE ❌ (empty)                                    │
│  └─ Return 404 ❌                                                   │
│                                                                      │
│  Invocation 3: Poll status                                          │
│  ├─ Check IMAGE_CACHE ❌ (still empty)                              │
│  └─ Return 404 ❌                                                   │
│                                                                      │
│  Result: ❌ Status endpoint broken                                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    AFTER (Fixed)                                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Invocation 1: Generate image                                       │
│  ├─ Store in IMAGE_CACHE ✅                                         │
│  ├─ Store in DynamoDB ✅                                            │
│  └─ Lambda ends (memory freed, data persists)                       │
│                                                                      │
│  Invocation 2: Poll status                                          │
│  ├─ Check IMAGE_CACHE ❌ (empty)                                    │
│  ├─ Check DynamoDB ✅ (found!)                                      │
│  └─ Return status ✅                                                │
│                                                                      │
│  Invocation 3: Poll status                                          │
│  ├─ Check IMAGE_CACHE ❌ (empty)                                    │
│  ├─ Check DynamoDB ✅ (found!)                                      │
│  └─ Return status ✅                                                │
│                                                                      │
│  Result: ✅ Status endpoint works!                                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📈 Performance Impact

```
┌──────────────────────────────────────────────────────────────────────┐
│                    LATENCY COMPARISON                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Operation              Before    After     Impact                  │
│  ─────────────────────────────────────────────────────────────────  │
│  Store image            <1ms      10-50ms   +10-50ms (acceptable)   │
│  Get status             <1ms      10-50ms   +10-50ms (acceptable)   │
│  Retrieve image         <1ms      10-50ms   +10-50ms (acceptable)   │
│  ─────────────────────────────────────────────────────────────────  │
│  Total (generate)       15-20s    15-20s    No change               │
│  Total (poll)           <1s       10-50ms   Slightly slower         │
│  Total (retrieve)       <1s       10-50ms   Slightly slower         │
│                                                                      │
│  Note: DynamoDB latency is negligible compared to image generation  │
│        (10-15 seconds), so overall user experience is unchanged.    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Summary

**The Problem:**
- Lambda invocations are stateless
- In-memory cache is lost between invocations
- Status endpoint returns 404 on new invocation

**The Solution:**
- Add DynamoDB for persistent storage
- Check memory first (fast), then DynamoDB (persistent)
- Data survives across Lambda invocations

**The Result:**
- ✅ Status endpoint works correctly
- ✅ Payment polling works
- ✅ Image retrieval works
- ✅ No performance degradation

---

*Visual Diagrams for 404 Status Endpoint Fix - Fulmine-Sparks*
