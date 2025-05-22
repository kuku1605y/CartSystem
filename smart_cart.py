import tkinter as tk
from tkinter import ttk, messagebox
from firebase_service import db
from datetime import datetime
import random
import queue
import threading

class SmartCartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Cart System")
        
        # Setup queue for thread-safe GUI updates
        self.update_queue = queue.Queue()
        self.root.after(100, self.process_updates)
        
        # Cart Treeview with selection enabled
        self.tree = ttk.Treeview(root, columns=("Name", "Price", "Qty"), show="headings", selectmode='browse')
        self.tree.heading("Name", text="Product")
        self.tree.heading("Price", text="Price")
        self.tree.heading("Qty", text="Qty")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control Frame at bottom
        control_frame = tk.Frame(root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Quantity controls
        qty_frame = tk.Frame(control_frame)
        qty_frame.pack(side=tk.LEFT, padx=5)
        
        self.btn_minus = tk.Button(qty_frame, text="-", width=3, command=self.decrease_qty)
        self.btn_plus = tk.Button(qty_frame, text="+", width=3, command=self.increase_qty)
        self.btn_minus.pack(side=tk.LEFT)
        self.btn_plus.pack(side=tk.LEFT)
        
        # Clear Cart button
        self.clear_btn = tk.Button(control_frame, text="Clear Cart", command=self.clear_cart)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Checkout Button
        self.checkout_btn = tk.Button(control_frame, text="Checkout", command=self.show_checkout)
        self.checkout_btn.pack(side=tk.RIGHT)
        
        # Initialize
        self.load_cart()
        self.selected_item = None
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)

    def on_item_select(self, event):
        """Handle item selection"""
        selected = self.tree.selection()
        self.selected_item = selected[0] if selected else None

    def process_updates(self):
        """Process updates from the queue in the main thread"""
        while not self.update_queue.empty():
            task = self.update_queue.get()
            task()
        self.root.after(100, self.process_updates)

    def load_cart(self):
        """Load and monitor cart in real-time"""
        cart_ref = db.collection("carts").document("current")
        
        def listener(doc_snapshot, changes, read_time):
            cart = doc_snapshot[0].to_dict() if doc_snapshot else None
            self.update_queue.put(lambda: self.update_cart_display(cart))
        
        # Initial load
        cart = cart_ref.get().to_dict()
        self.update_queue.put(lambda: self.update_cart_display(cart))
        
        # Start listener in separate thread
        threading.Thread(
            target=cart_ref.on_snapshot,
            args=(listener,),
            daemon=True
        ).start()

    def update_cart_display(self, cart):
        """Update the cart display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add new items if cart exists
        if cart and "items" in cart:
            for item in cart["items"]:
                self.tree.insert("", tk.END, values=(
                    item["name"],
                    f"₹ {item['price']:.2f}",
                    item["quantity"]
                ), tags=(item["barcode"],))

    def get_selected_barcode(self):
        """Get barcode of selected item"""
        if not self.selected_item:
            return None
        return self.tree.item(self.selected_item, "tags")[0]

    def update_quantity(self, barcode, change):
        """Update item quantity in Firebase"""
        def update_task():
            cart_ref = db.collection("carts").document("current")
            cart = cart_ref.get().to_dict()
            
            if not cart or "items" not in cart:
                return
                
            for item in cart["items"]:
                if item["barcode"] == barcode:
                    new_qty = item["quantity"] + change
                    if new_qty > 0:
                        item["quantity"] = new_qty
                    else:
                        cart["items"].remove(item)
                    break
                    
            cart_ref.update({"items": cart["items"]})
        
        threading.Thread(target=update_task, daemon=True).start()

    def increase_qty(self):
        """Increase quantity of selected item"""
        barcode = self.get_selected_barcode()
        if barcode:
            self.update_quantity(barcode, 1)
        else:
            messagebox.showwarning("Warning", "Please select an item first")

    def decrease_qty(self):
        """Decrease quantity of selected item"""
        barcode = self.get_selected_barcode()
        if barcode:
            self.update_quantity(barcode, -1)
        else:
            messagebox.showwarning("Warning", "Please select an item first")

    def clear_cart(self):
        """Clear all items from cart"""
        if messagebox.askyesno("Confirm", "Clear all items from cart?"):
            db.collection("carts").document("current").update({"items": []})

    def show_checkout(self):
        """Show checkout form window"""
        cart_ref = db.collection("carts").document("current")
        cart = cart_ref.get().to_dict()
        
        if not cart or not cart.get("items"):
            messagebox.showerror("Error", "Cart is empty")
            return
            
        checkout_win = tk.Toplevel(self.root)
        checkout_win.title("Customer Details")
        
        # Form fields
        tk.Label(checkout_win, text="Customer Name:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = tk.Entry(checkout_win)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(checkout_win, text="Phone No.:").grid(row=1, column=0, padx=5, pady=5)
        phone_entry = tk.Entry(checkout_win)
        phone_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Submit button
        tk.Button(checkout_win, text="Complete Purchase",
                 command=lambda: self.process_checkout(
                     name_entry.get(),
                     phone_entry.get(),
                     checkout_win
                 )).grid(row=2, columnspan=2, pady=10)

    def process_checkout(self, name, phone, window):
        """Generate invoice and clear cart"""
        if not name or not phone:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        cart_ref = db.collection("carts").document("current")
        cart = cart_ref.get().to_dict()
        
        if not cart or not cart.get("items"):
            messagebox.showerror("Error", "Cart is empty")
            return
            
        # Generate invoice
        invoice_data = {
            "invoice_number": self.generate_invoice_number(),
            "customer_name": name,
            "customer_phone": phone,
            "items": cart["items"],
            "total": sum(item["price"] * item["quantity"] for item in cart["items"]),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "paid"
        }
        
        # Save to Firebase
        db.collection("invoices").add(invoice_data)
        cart_ref.update({"items": []})
        
        # Show success
        messagebox.showinfo("Success", f"Invoice #{invoice_data['invoice_number']} generated!")
        window.destroy()
        
        # Print invoice (optional)
        self.print_invoice(invoice_data)

    def generate_invoice_number(self):
        """Generate unique invoice number"""
        return f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

    def print_invoice(self, invoice):
        """Display invoice in new window"""
        invoice_win = tk.Toplevel(self.root)
        invoice_win.title(f"Invoice #{invoice['invoice_number']}")
        
        # Header
        tk.Label(invoice_win, 
                text=f"INVOICE #{invoice['invoice_number']}",
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Customer info
        tk.Label(invoice_win, 
                text=f"Customer: {invoice['customer_name']}\nPhone: {invoice['customer_phone']}",
                justify=tk.LEFT).pack(anchor=tk.W, padx=20)
        
        # Items table
        tree = ttk.Treeview(invoice_win, columns=("Item", "Price", "Qty", "Subtotal"), show="headings")
        tree.heading("Item", text="Item")
        tree.heading("Price", text="Price")
        tree.heading("Qty", text="Qty")
        tree.heading("Subtotal", text="Subtotal")
        
        for item in invoice["items"]:
            subtotal = item["price"] * item["quantity"]
            tree.insert("", tk.END, values=(
                item["name"],
                f"₹ {item['price']:.2f}",
                item["quantity"],
                f"₹ {subtotal:.2f}"
            ))
        
        tree.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Total
        tk.Label(invoice_win, 
                text=f"TOTAL: ₹ {invoice['total']:.2f}",
                font=("Arial", 12, "bold")).pack(pady=10)
        
        # Close button
        tk.Button(invoice_win, text="Close", command=invoice_win.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = SmartCartApp(root)
    root.mainloop()