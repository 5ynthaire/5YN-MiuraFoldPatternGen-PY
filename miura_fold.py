import argparse
import math

DPI = 96
PX_PER_MM = DPI / 25.4

def parse_dim_str(s):
    parts = s.split('x')
    if len(parts) != 2:
        raise ValueError("Invalid format: expected wxh")
    return float(parts[0]), float(parts[1])

def generate_miura_svg(mm_w, mm_h, compact, folds_color, folds_dotted, theta):
    target_theta = theta  # User-specified; flexes internally via fitting
    px_w = mm_w * PX_PER_MM
    px_h = mm_h * PX_PER_MM
    svg = f'<svg width="{mm_w:.2f}mm" height="{mm_h:.2f}mm" viewBox="0 0 {px_w:.0f} {px_h:.0f}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Determine orientation
    if mm_h > mm_w:  # portrait
        LE_mm = mm_h
        SE_mm = mm_w
        is_portrait = True
    else:
        LE_mm = mm_w
        SE_mm = mm_h
        is_portrait = False
    
    PSL_mm = SE_mm / compact
    target_PF_mm = PSL_mm * math.sin(math.radians(target_theta))
    num_rows = round(LE_mm / target_PF_mm)
    PF_spacing_mm = LE_mm / num_rows
    if PF_spacing_mm > PSL_mm:
        num_rows += 1
        PF_spacing_mm = LE_mm / num_rows
    theta_rad = math.asin(PF_spacing_mm / PSL_mm)
    theta_deg = math.degrees(theta_rad)
    offset_mm = math.cos(theta_rad) * PSL_mm
    
    PF_spacing = PF_spacing_mm * PX_PER_MM
    offset = offset_mm * PX_PER_MM
    JF_spacing = PSL_mm * PX_PER_MM  # since PSL = JF spacing
    
    num_cols = compact
    
    # Rendering mode
    use_colors = folds_color is not None
    use_dotted = folds_dotted
    use_folds = use_colors or use_dotted  # Parity for colors/dashes
    color_m = folds_color[0] if use_colors else 'black'
    color_v = folds_color[1] if use_colors else 'black'
    dash_m = '1,2,4,2' if use_dotted else None  # Morse: dot-gap-dash-gap
    dash_v = '3,3' if use_dotted else None  # segment-dash for V (kept visible/distinct)
    
    if is_portrait:
        # PF: horizontal segments (vertex-to-vertex, shifted on odd rows)
        for i in range(num_rows + 1):
            y = i * PF_spacing
            row_parity = (i % 2 == 0)
            shift = offset if not row_parity else 0  # Shift for odd rows
            for j in range(num_cols):
                x_start = j * JF_spacing + shift
                x_end = (j + 1) * JF_spacing + shift
                # Clip to viewBox
                x_start = min(x_start, px_w)
                x_end = min(x_end, px_w)
                left_jf_m = (j % 2 == 0)
                is_m = left_jf_m != row_parity
                color = color_m if is_m and use_colors else color_v if not is_m and use_colors else 'black'
                dash = dash_m if is_m and use_dotted else dash_v if not is_m and use_dotted else None
                dash_str = f' stroke-dasharray="{dash}"' if dash else ''
                svg += f'  <line x1="{x_start:.3f}" y1="{y:.3f}" x2="{x_end:.3f}" y2="{y:.3f}" stroke="{color}" stroke-width="0.25"{dash_str}/>\n'
        
        # JF: zigzag paths, unidirectional shift (+offset on odd rows), clip x
        for col in range(num_cols):
            x_base = col * JF_spacing
            parity = (col % 2 == 0)
            path_color = color_m if parity and use_colors else color_v if not parity and use_colors else 'black'
            path_dash = dash_m if parity and use_dotted else dash_v if not parity and use_dotted else None
            dash_str = f' stroke-dasharray="{path_dash}"' if path_dash else ''
            for row in range(num_rows):
                y_start = row * PF_spacing
                y_end = (row + 1) * PF_spacing
                if row % 2 == 0:
                    x_start = x_base
                    x_end = x_base + offset
                else:
                    x_start = x_base + offset
                    x_end = x_base
                x_end = min(x_end, px_w)  # Clip
                svg += f'  <line x1="{x_start:.3f}" y1="{y_start:.3f}" x2="{x_end:.3f}" y2="{y_end:.3f}" stroke="{path_color}" stroke-width="0.25"{dash_str}/>\n'
    else:
        # Landscape: PF vertical segments (vertex-to-vertex, shifted on odd rows)
        for i in range(num_rows + 1):
            x = i * PF_spacing
            row_parity = (i % 2 == 0)
            shift = offset if not row_parity else 0
            for j in range(num_cols):
                y_start = j * JF_spacing + shift
                y_end = (j + 1) * JF_spacing + shift
                y_start = min(y_start, px_h)
                y_end = min(y_end, px_h)
                left_jf_m = (j % 2 == 0)
                is_m = left_jf_m != row_parity
                color = color_m if is_m and use_colors else color_v if not is_m and use_colors else 'black'
                dash = dash_m if is_m and use_dotted else dash_v if not is_m and use_dotted else None
                dash_str = f' stroke-dasharray="{dash}"' if dash else ''
                svg += f'  <line x1="{x:.3f}" y1="{y_start:.3f}" x2="{x:.3f}" y2="{y_end:.3f}" stroke="{color}" stroke-width="0.25"{dash_str}/>\n'
        
        # JF: horizontal zigzags, clip y
        for col in range(num_cols):
            y_base = col * JF_spacing
            parity = (col % 2 == 0)
            path_color = color_m if parity and use_colors else color_v if not parity and use_colors else 'black'
            path_dash = dash_m if parity and use_dotted else dash_v if not parity and use_dotted else None
            dash_str = f' stroke-dasharray="{path_dash}"' if path_dash else ''
            for row in range(num_rows):
                x_start = row * PF_spacing
                x_end = (row + 1) * PF_spacing
                if row % 2 == 0:
                    y_start = y_base
                    y_end = y_base + offset
                else:
                    y_start = y_base + offset
                    y_end = y_base
                y_end = min(y_end, px_h)
                svg += f'  <line x1="{x_start:.3f}" y1="{y_start:.3f}" x2="{x_end:.3f}" y2="{y_end:.3f}" stroke="{path_color}" stroke-width="0.25"{dash_str}/>\n'
    
    svg += '</svg>'
    return svg, theta_deg  # Return theta for print

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Miura-ori crease pattern SVG")
    parser.add_argument('--mm', type=str, help='Dimensions in mm: wxh')
    parser.add_argument('--inches', type=str, help='Dimensions in inches: wxh')
    parser.add_argument('--px', type=str, default='816x1056', help='Dimensions in px: wxh (default: letter portrait at 96 DPI)')
    parser.add_argument('--compact', type=int, default=7, help='Compactness factor (default: 7)')
    parser.add_argument('--theta', type=float, default=60, help='Target angle in degrees (60-80; default 60)')
    parser.add_argument('--folds-color', nargs=2, default=None, help='M/V colors as hex1 hex2 (e.g., #00FF00 #FF00FF)')
    parser.add_argument('--folds-dotted', action='store_true', help='Enable dotted lines for M/V (Morse for M, segment-dash for V; black if no colors)')
    parser.add_argument('--output', type=str, default='miura_fold.svg', help='Output SVG file (default: miura_fold.svg)')
    args = parser.parse_args()
    
    # Clamp theta to 60-80
    args.theta = max(60, min(80, args.theta))
    
    folds_color = args.folds_color  # List of 2 or None
    
    # Collect valid dimensions
    dims = []
    if args.mm:
        try:
            w, h = parse_dim_str(args.mm)
            dims.append(('mm', w, h))
        except ValueError:
            pass
    if args.inches:
        try:
            w, h = parse_dim_str(args.inches)
            w_mm = w * 25.4
            h_mm = h * 25.4
            dims.append(('inches', w_mm, h_mm))
        except ValueError:
            pass
    if args.px:
        try:
            w, h = parse_dim_str(args.px)
            w_mm = w * 25.4 / DPI
            h_mm = h * 25.4 / DPI
            dims.append(('px', w_mm, h_mm))
        except ValueError:
            pass
    
    if not dims:
        parser.error("No valid dimensions provided")
    
    if len(dims) > 1:
        print(f"Multiple valid dimensions detected; using first: {dims[0][0]} {dims[0][1]:.1f}x{dims[0][2]:.1f}mm")
    
    mm_w, mm_h = dims[0][1], dims[0][2]
    
    svg, theta_final = generate_miura_svg(mm_w, mm_h, args.compact, folds_color, args.folds_dotted, args.theta)
    
    with open(args.output, 'w') as f:
        f.write(svg)
    
    print(f"Miura-ori pattern generated: {args.output}")
    print(f"Dimensions: {mm_w:.1f} x {mm_h:.1f} mm")
    print(f"Compactness: {args.compact}")
    print(f"Final theta: {theta_final:.1f}° (target {args.theta}°)")
    if folds_color:
        print(f"Folds colors: M={folds_color[0]}, V={folds_color[1]}")
    if args.folds_dotted:
        print("Dotted lines enabled (Morse M, segment-dash V)")
