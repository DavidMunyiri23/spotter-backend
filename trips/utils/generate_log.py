from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings
from datetime import datetime, timedelta


def generate_log_sheet(date, duty_periods, output_path=None):
    """
    Generate a daily log sheet with duty periods overlaid on a grid
    
    Args:
        date: Date for the log sheet
        duty_periods: List of duty periods with start_time, end_time, and duty_type
        output_path: Optional path to save the image
    
    Returns:
        Path to the generated image
    """
    # Create a blank log sheet (800x600 pixels)
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 12)
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Draw title
    title = f"Daily Log Sheet - {date.strftime('%B %d, %Y')}"
    draw.text((20, 20), title, font=title_font, fill='black')
    
    # Draw 24-hour grid
    grid_start_y = 80
    grid_height = 400
    grid_start_x = 80
    grid_width = 600
    
    # Draw time labels and grid lines
    for hour in range(25):  # 0 to 24 hours
        x = grid_start_x + (hour * grid_width // 24)
        draw.line([(x, grid_start_y), (x, grid_start_y + grid_height)], fill='lightgray', width=1)
        if hour % 2 == 0:  # Show label every 2 hours
            time_label = f"{hour:02d}:00"
            draw.text((x - 15, grid_start_y - 20), time_label, font=font, fill='black')
    
    # Draw duty status rows
    duty_types = ['Off Duty', 'Sleeper Berth', 'Driving', 'On Duty (Not Driving)']
    row_height = grid_height // 4
    
    for i, duty_type in enumerate(duty_types):
        y = grid_start_y + (i * row_height)
        # Draw horizontal line
        draw.line([(grid_start_x, y), (grid_start_x + grid_width, y)], fill='black', width=1)
        # Draw duty type label
        draw.text((10, y + row_height // 2 - 10), duty_type, font=font, fill='black')
    
    # Draw bottom line
    draw.line([(grid_start_x, grid_start_y + grid_height), 
               (grid_start_x + grid_width, grid_start_y + grid_height)], fill='black', width=2)
    
    # Draw duty periods
    duty_colors = {
        'off_duty': 'blue',
        'sleeper_berth': 'green',
        'driving': 'red',
        'on_duty': 'orange'
    }
    
    for period in duty_periods:
        duty_type = period.get('duty_type', 'off_duty')
        start_hour = period.get('start_hour', 0)
        end_hour = period.get('end_hour', 0)
        
        # Calculate position
        start_x = grid_start_x + (start_hour * grid_width // 24)
        end_x = grid_start_x + (end_hour * grid_width // 24)
        
        # Determine row based on duty type
        if duty_type == 'off_duty':
            row = 0
        elif duty_type == 'sleeper_berth':
            row = 1
        elif duty_type == 'driving':
            row = 2
        else:  # on_duty
            row = 3
        
        y = grid_start_y + (row * row_height) + 5
        line_y = y + row_height // 2 - 5
        
        # Draw duty period line
        color = duty_colors.get(duty_type, 'black')
        draw.line([(start_x, line_y), (end_x, line_y)], fill=color, width=4)
    
    # Add summary information
    summary_y = grid_start_y + grid_height + 50
    draw.text((20, summary_y), "Total Hours Summary:", font=title_font, fill='black')
    
    # Calculate totals from duty periods
    totals = {'off_duty': 0, 'sleeper_berth': 0, 'driving': 0, 'on_duty': 0}
    for period in duty_periods:
        duty_type = period.get('duty_type', 'off_duty')
        hours = period.get('end_hour', 0) - period.get('start_hour', 0)
        totals[duty_type] += hours
    
    summary_text = [
        f"Off Duty: {totals['off_duty']:.1f} hours",
        f"Sleeper Berth: {totals['sleeper_berth']:.1f} hours",
        f"Driving: {totals['driving']:.1f} hours",
        f"On Duty (Not Driving): {totals['on_duty']:.1f} hours"
    ]
    
    for i, text in enumerate(summary_text):
        draw.text((20, summary_y + 30 + (i * 20)), text, font=font, fill='black')
    
    # Save the image
    if not output_path:
        # Create media directory if it doesn't exist
        media_dir = os.path.join(settings.MEDIA_ROOT, 'log_sheets')
        os.makedirs(media_dir, exist_ok=True)
        filename = f"log_sheet_{date.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}.png"
        output_path = os.path.join(media_dir, filename)
    
    img.save(output_path, 'PNG')
    return output_path


def create_sample_log_sheet():
    """Create a sample log sheet for testing"""
    from datetime import date
    
    sample_periods = [
        {'duty_type': 'off_duty', 'start_hour': 0, 'end_hour': 8},
        {'duty_type': 'on_duty', 'start_hour': 8, 'end_hour': 9},
        {'duty_type': 'driving', 'start_hour': 9, 'end_hour': 18},
        {'duty_type': 'off_duty', 'start_hour': 18, 'end_hour': 24},
    ]
    
    return generate_log_sheet(date.today(), sample_periods)