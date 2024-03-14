import svgwrite
import barcode
from barcode.writer import SVGWriter
import os
from json import loads
from datetime import datetime

config_data = loads(open('config.json').read())
store_logo_path = 'assets/rbf_logo.png'

class StickerGenerator:

    def __init__(self, products, svg_file_path):
        self.products = products
        self.svg_file_path = svg_file_path
        self.sticker_width, self.sticker_height = 75, 50
        self.dflt_font_size, self.mrp_font_size, self.discount_font_size = 14, 18, 22
        self.barcode_max_len = config_data['billing']['barcode_max_len']
        self.temp_fold = 'temp'
        os.makedirs(self.temp_fold, exist_ok=True)

    def generate_stickers(self):

        gap_width_mm = 0  # 5mm gap
        canvas_height_mm = (self.sticker_height + gap_width_mm) * len(self.products) - gap_width_mm
        canvas_width_mm = self.sticker_width

        # Create an SVG drawing for the canvas
        canvas = svgwrite.Drawing(self.svg_file_path, profile='tiny', size=(f'{canvas_width_mm}mm', f'{canvas_height_mm}mm'))

        # Generate and arrange stickers on the canvas
        y_offset = 0

        for product in self.products:
            product_id = str(product['product_id']).zfill(self.barcode_max_len)
            product_name = product['product_name']
            product_size = product['product_size']
            product_color = product['product_color']
            mrp = product['product_mrp']
            discounted_price = round(product['product_discounted_price'], 2)

            logo = canvas.image(store_logo_path, size=('30mm', f'{self.sticker_height - 25}mm'), insert=('3mm', f'{y_offset}mm'), preserveAspectRatio='xMidYMid meet')
            logo.set_desc('Company Logo')
            canvas.add(logo)

            canvas.add(canvas.text(f"Item:" , insert=('35mm', f'{y_offset + 6}mm'), font_size=self.dflt_font_size, fill='black'))
            canvas.add(canvas.text(f"{product_name}", insert=('45mm', f'{y_offset + 6}mm'), font_size=self.dflt_font_size, fill='black', font_weight='bold'))

            canvas.add(canvas.text(f"Size:", insert=('35mm', f'{y_offset + 10}mm'), font_size=self.dflt_font_size, fill='black'))
            canvas.add(canvas.text(f"{product_size}", insert=('45mm', f'{y_offset + 10}mm'), font_size=self.dflt_font_size, fill='black', font_weight='bold'))

            canvas.add(canvas.text(f"Color:", insert=('35mm', f'{y_offset + 14}mm'), font_size=self.dflt_font_size, fill='black'))
            canvas.add(canvas.text(f"{product_color}", insert=('45mm', f'{y_offset + 14}mm'), font_size=self.dflt_font_size, fill='black', font_weight='bold'))

            mrp, discounted_price = round(float(mrp), 2), round(float(discounted_price), 2)
            canvas.add(canvas.text(f"MRP:", insert=('35mm', f'{y_offset + 21.5}mm'), font_size=self.dflt_font_size, fill='black'))
            canvas.add(canvas.text(f"₹ {mrp}", insert=('45mm', f'{y_offset + 21.5}mm'), font_size=self.mrp_font_size, fill='black', font_weight='bold'))

            canvas.add(canvas.text(f"Discount Price:", insert=('6.5mm', f'{y_offset + 29}mm'), font_size=self.dflt_font_size, fill='black'))
            canvas.add(canvas.text(f"₹ {discounted_price}/- Only", insert=('34mm', f'{y_offset + 29}mm'), font_size=self.discount_font_size, fill='black', font_weight='bold'))
            canvas.add(canvas.text(f"(Incl of all taxes)", insert=('32mm', f'{y_offset + 33}mm'), font_size=self.dflt_font_size, fill='black'))

            render_options = {
                'module_width': 0.4,
                'module_height': 10.0,
                'font_size': 12,
                }
            barcode.generate('code128', product_id, writer=SVGWriter(), output=f'{self.temp_fold}/{product_id}_barcode', writer_options=render_options)
            # Add the barcode image below the company name
            barcode_image = canvas.image(f'{self.temp_fold}/{product_id}_barcode.svg', insert=('10mm', f'{y_offset + self.sticker_height - 15}mm'), size=(f'{self.sticker_width - 20}mm', '15mm'))
            barcode_image.set_desc('Barcode')
            canvas.add(barcode_image)

            y_offset += self.sticker_height + gap_width_mm

        canvas.save()

class EscPosCmdGenerator:

    def __init__(self, bill_no, emp_id, table_data, discount, payment_details):
        self.bill_no = bill_no
        self.emp_id = emp_id
        self.table_data = table_data        # list of lists -- [id, desc, qty, price, total, gst] where price is discounted price
        self.discount = discount
        self.payment_details = payment_details  # tuple of strings mode-amount

    def generate_esc_pos_cmds(self):

        store_details = config_data['store']

        col1_end_pos = 10
        col2_end_pos = 22
        col3_end_pos = 31
        col4_end_pos = 41

        # store details
        esc_pos_commands = [
            b'\x1B\x40',                  # Initialize printer
            b'\x1B\x61\x01',              # Center align text
            b'\x1B\x21\x30',              # Double height and width text
            store_details['store_name'].encode('utf-8'),
            b'\n'
            b'\x1B\x21\x00',              # Reset to normal text size
            store_details['store_address1'].encode('utf-8'),
            b'\n',
            store_details['store_address2'].encode('utf-8'),
            b'\n',
            f'Phone: {store_details["store_phone"]}'.encode('utf-8'),
            b'\n',
            f'GSTIN: {store_details["store_gstin"]}'.encode('utf-8'),
            b'\n',
            b'\x1B\x61\x00',
            b'------------------------------------------------\n',
            b'\x1B\x61\x01',              # Center align text
            b'\x1B\x45\x01',              # Bold text
            b'\x1B\x21\x30',              # Double height and width text
            b'TAX INVOICE\n',
            b'\x1B\x21\x00',              # Reset to normal text size
            b'\x1B\x45\x00',              # Normal text
            b'\x1B\x61\x00',              # Left align text
            b'------------------------------------------------\n',

            f' Bill No: {self.bill_no} Date: {datetime.now().strftime("%d/%m/%Y-%H:%M:%S")}\n'.encode('utf-8'),
            f' Cashier: {self.emp_id}\n'.encode('utf-8'),
            b'\x1B\x45\x01'
            b'+----------------------------------------------+\n',  # Top border of the table
            b'| id                  Qty     Price      Total |\n',  # Header row
            b'|----------------------------------------------|\n',  # Header row separator
            b'\x1B\x45\x00'                                         # Normal text
            b'\x1B\x61\x00'           # Left align text
        ]


        def add_row_to_commands(id, desc, qty, price, total, gst, commands):
            # Create a format string for the row
            id, qty, price, total = str(id), str(qty), str(round(float(price), 2)), str(round(float(total), 2))

            price = f'{float(price):.2e}' if len(price) > 8 else price
            total = f'{float(total):.2e}' if len(total) > 8 else total

            id = str(id).zfill(7)

            row_format = f'| {id:<{col1_end_pos}} {qty:>{col2_end_pos - col1_end_pos}} {price:>{col3_end_pos - col2_end_pos}} {total:>{col4_end_pos - col3_end_pos}} |\n'
            
            # Append the formatted row to the existing commands
            commands.append(row_format.encode('utf-8'))
            #append description
            commands.append(f'  {desc}\n'.encode('utf-8'))
            taxable_amt = round(float(total)/(1 + gst/100), 2)
            taxable_amt = f'{taxable_amt:.2e}' if len(str(taxable_amt)) > 8 else taxable_amt
            commands.append(f'  Taxable Value: {taxable_amt} CGST@{round(gst/2, 2)}% SGST@{round(gst/2, 2)}%\n'.encode('utf-8'))
            commands.append(b'|----------------------------------------------|\n')
            return commands

        # Add each row of data to the existing commands
        total_items_org, total_qty_org, total_price_org = 0, 0, 0.0
        gst_details = {}
        for row in self.table_data:
            esc_pos_commands = add_row_to_commands(row[0], row[1], row[2], row[3], row[4], row[5], esc_pos_commands)
            total_items_org += 1
            total_qty_org += row[2]
            total_price_org += row[4]
            taxable_amt = round(float(row[4])/(1 + row[5]/100), 2)
            if row[5] not in gst_details:
                gst_details[row[5]] = {'taxable_amt': taxable_amt, 'cgst': round(taxable_amt*row[5]/200, 2), 'sgst': round(taxable_amt*row[5]/200, 2), 'total': round(row[4], 2)}
            else:
                gst_details[row[5]]['taxable_amt'] += taxable_amt
                gst_details[row[5]]['cgst'] += round(taxable_amt*row[5]/200, 2)
                gst_details[row[5]]['sgst'] += round(taxable_amt*row[5]/200, 2)
                gst_details[row[5]]['total'] += round(row[4], 2)

        total_items, total_qty = int(total_items_org), int(total_qty_org)
        total_price = f'{total_price_org:.2e}' if len(str(total_price_org)) > 8 else round(total_price_org, 2)
        net_total_diplay = int(total_price_org - self.discount)

        esc_pos_commands += (
            f'  Discount: {round(self.discount, 2)}\n'.encode('utf-8'),
            b'|----------------------------------------------|\n'
            #bold text
            b'\x1B\x45\x01',
            # increase font size
            b'\x1B\x21\x12',
            # align center
            b'\x1B\x61\x01',
            b'  Items: ' + str(total_items).encode('utf-8') + b'    Qty: ' + str(total_qty).encode('utf-8') + b'    NetTotal: ' + str(net_total_diplay).encode('utf-8') + b'\n',
            # align left
            b'\x1B\x61\x00',
            # normal font size
            b'\x1B\x21\x00',
            b'\x1B\x45\x01',
            b'+----------------------------------------------+\n\n',  # Bottom border of the table
            b'<-------------GST Breakup Details-------------->\n',
            b'+----------------------------------------------+\n',
            b'| Taxable Value      CGST      SGST      Total |\n',
            b'|----------------------------------------------|\n',
            b'\x1B\x45\x00'
        )

            
        total_taxable_amt_org, total_cgst_org, total_sgst_org = 0.0, 0.0, 0.0
        for gst, gst_detail in gst_details.items():
            taxable_amt = round(gst_detail['taxable_amt'], 2)
            cgst = round(float(gst_detail['cgst']), 2)
            sgst = round(float(gst_detail['sgst']), 2)
            total = round(float(gst_detail['total']), 2)
            total_taxable_amt_org += taxable_amt
            total_cgst_org += cgst
            total_sgst_org += sgst
            taxable_amt = f'{taxable_amt:.2e}' if len(str(taxable_amt)) > 8 else taxable_amt
            cgst = f'{cgst:.2e}' if len(str(cgst)) > 8 else cgst
            sgst = f'{sgst:.2e}' if len(str(sgst)) > 8 else sgst
            total = f'{total:.2e}' if len(str(total)) > 8 else total
            esc_pos_commands.append(f'  CGST@{round(gst/2, 2)}% SGST@{round(gst/2, 2)}%\n'.encode('utf-8'))
            cmd = f'| {taxable_amt:<{col1_end_pos}} {cgst:>{col2_end_pos - col1_end_pos}} {sgst:>{col3_end_pos - col2_end_pos}} {total:>{col4_end_pos - col3_end_pos}} |\n'
            esc_pos_commands.append(cmd.encode('utf-8'))
            esc_pos_commands.append(b'|----------------------------------------------|\n')

        total_taxable_amt = f'{total_taxable_amt_org:.2e}' if len(str(round(total_taxable_amt_org, 2))) > 8 else round(total_taxable_amt_org, 2)
        total_cgst = f'{total_cgst_org:.2e}' if len(str(total_cgst_org)) > 8 else round(total_cgst_org, 2)
        total_sgst = f'{total_sgst_org:.2e}' if len(str(total_sgst_org)) > 8 else round(total_sgst_org, 2)

        total_tax_cmd = f'| {total_taxable_amt:<{col1_end_pos}} {total_cgst:>{col2_end_pos - col1_end_pos}} {total_sgst:>{col3_end_pos - col2_end_pos}} {total_price:>{col4_end_pos - col3_end_pos}} |\n'
        esc_pos_commands += (
            b'\x1B\x45\x01',
            b'\x1B\x21\x08',
            total_tax_cmd.encode('utf-8'),
            b'\x1B\x45\x00',
            b'+----------------------------------------------+\n',
        )

        # Payment details
        payment_cmd = ''
        for payment_detail in self.payment_details:
            mode, amount = payment_detail.split('-')[0], round(float(payment_detail.split('-')[1]), 2)
            payment_cmd += f'  {mode:<{col1_end_pos}} {amount:>{col4_end_pos - col1_end_pos}}\n'
        esc_pos_commands += (
            b'\n',
            b'------------------------------------------------\n',
            b'\x1B\x61\x01',              # Center align text
            b'\x1B\x45\x01',              # Bold text
            f'Payment Details\n'.encode('utf-8'),
            b'------------------------------------------------\n',
            b'\x1B\x45\x00',              # Normal text
            b'\x1B\x61\x00',              # Left align text
            payment_cmd.encode('utf-8'),
            b'------------------------------------------------\n\n',
            b'\x1B\x61\x01',              # Center align text
            b'\x1B\x45\x01',              # Bold text
            f'Thank you for your business!\n'.encode('utf-8'),
            b'\x1B\x45\x00',              # Normal text
            b'\x1B\x61\x00',              # Left align text
            b'\x1D\x56\x41\x10',          # Cut paper (partial cut)



        )
        #     b'\n',
        #     b'Thank you for your business!\n',
        #     b'\x1B\x61\x00',              # Left align text
        #     b'\x1D\x56\x41\x10',          # Cut paper (partial cut)
        # )

        return esc_pos_commands
