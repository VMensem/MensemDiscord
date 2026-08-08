import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

class ProfileGenerator:
    def __init__(self):
        self.background_path = "profiles/assets/background.png"
        self.font_path = "profiles/assets/fonts/font.ttf"  # Need to ensure this exists

    async def generate(self, user, stats):
        # Create a blank image 1600x600
        # For now, let's just create a basic image and add text.
        # Premium features (glow, blur) will be added step by step.
        
        # Load background
        bg = Image.open(self.background_path).convert("RGBA")
        
        # Create a new image for the HUD elements
        hud = Image.new("RGBA", (1600, 600), (0, 0, 0, 0))
        draw = ImageDraw.Draw(hud)
        
        # Example: Drawing a rectangle for the left panel (Glassmorphism effect)
        # Glassmorphism: Semi-transparent black with blur
        panel = Image.new("RGBA", (400, 520), (0, 0, 0, 128))
        # Drawing panel with rounded corners (simplified for now)
        hud.paste(panel, (40, 40))
        
        # Add text
        font_large = ImageFont.truetype(self.font_path, 60)
        draw.text((460, 100), f"{user.name}", fill="white", font=font_large)
        
        # Composite
        final_image = Image.alpha_composite(bg, hud)
        
        # Save to buffer
        buffer = io.BytesIO()
        final_image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
