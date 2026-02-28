# Running the Fulmine-Sparks Client

## Prerequisites

1. **Python 3.7+** installed on your system
2. **requests** module: `pip install requests`
3. **qrcode** module (optional, for QR codes): `pip install qrcode[pil]`

## Setup

### Windows

1. Open Command Prompt and navigate to the directory with `client.py`
2. Install dependencies:
   ```
   pip install requests qrcode[pil]
   ```

3. Run the client using the batch file:
   ```
   run_client.bat
   ```

   Or directly:
   ```
   python client.py
   ```

### Mac/Linux

1. Open Terminal
2. Install dependencies:
   ```
   pip3 install requests qrcode[pil]
   ```

3. Run the client:
   ```
   python3 client.py
   ```

## Usage

### Interactive Mode (No Arguments)
```
python client.py
```
This opens an interactive menu where you can:
- Check API health
- List available models
- Generate images
- Check image status
- Retrieve generated images
- Pay invoices
- Test rate limiting

### Command Line Mode

**Check Health:**
```
python client.py health
```

**List Models:**
```
python client.py models
```

**Generate Image:**
```
python client.py generate "A beautiful sunset over mountains" 1
```

**Check Status:**
```
python client.py status <payment_hash>
```

**Retrieve Image:**
```
python client.py retrieve <payment_hash>
```

**Pay Invoice:**
```
python client.py pay "lnbc..."
```

## How It Works

1. **Generate an image** - Creates an image and returns an invoice
2. **Pay with Lightning** - Scan the QR code or copy the invoice to pay
3. **Retrieve image** - Once payment is confirmed, retrieve your generated image

The workflow is now working without rate limiting blocking the image generation!
