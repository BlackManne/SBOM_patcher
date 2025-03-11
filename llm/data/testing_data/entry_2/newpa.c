

static void ti_break(struct tty_struct *tty, int break_state)
{
	struct usb_serial_port *port = tty->driver_data;
	struct ti_port *tport = usb_get_serial_port_data(port);
	int status;

	dev_dbg(&port->dev, "%s - state = %d\n", __func__, break_state);

	status = ti_write_byte(port, tport->tp_tdev,
		tport->tp_uart_base_addr + TI_UART_OFFSET_LCR,
		TI_LCR_BREAK, break_state == -1 ? TI_LCR_BREAK : 0);

	if (status)
		dev_dbg(&port->dev, "%s - error setting break, %d\n", __func__, status);
}