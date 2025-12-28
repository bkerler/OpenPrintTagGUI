import serial.tools.list_ports
import serial


# Function to get the port number from the port name
def get_port_number(port):
    try:
        return int(port.name[3:])
    except ValueError:
        return float('inf')  # For ports with non-numeric names, place them at the end


# Function to initialize the serial port
def initialize_serial_port(baudrate:int, target_vid:int, target_pid:int, logger=print):
    available_ports = serial.tools.list_ports.comports()

    matching_ports = [
        port for port in available_ports if port.vid == target_vid and port.pid == target_pid
    ]

    if not matching_ports:
        logger(f"No available serial ports found with VID:PID {target_vid}:{target_pid}.")
        return None, None

    # Sort ports by port number before presenting the selection menu
    matching_ports.sort(key=lambda port: get_port_number(port))

    if len(matching_ports) == 1:
        selected_port = matching_ports[0]
        serial_port = serial.Serial(selected_port.device, baudrate)
        logger(f"Connected to: {selected_port.device.ljust(6)} - Serial Number: {selected_port.serial_number}")
        return serial_port, selected_port

    print("Available COM ports:")
    for i, port in enumerate(matching_ports, start=1):
        print(f"{i}. {port.device.ljust(6)} - Serial Number: {port.serial_number}")

    while True:
        selected_port_index = input("Enter the number of the desired COM port (or type 'exit' to quit): ")

        if selected_port_index.lower() == 'exit':
            print("Exiting program.")
            return None, None

        try:
            selected_port_index = int(selected_port_index)
            if 1 <= selected_port_index <= len(matching_ports):
                selected_port = matching_ports[selected_port_index - 1]
                serial_port = serial.Serial(selected_port.device, baudrate)
                print(f"Connected to: {selected_port.device.ljust(6)} - Serial Number: {selected_port.serial_number}")
                print("Ready to collect data.")
                return serial_port, selected_port
            else:
                print("Invalid input. Please enter a valid number or type 'exit' to quit.")
        except ValueError:
            print("Invalid input. Please enter a valid number or type 'exit' to quit.")


# Function to filter unwanted characters from data
def filter_data(data_list):
    return [element.replace("(", "").replace(")", "") for element in data_list]


def collect_data(logger=print):
    # Configure the serial port
    target_vid = 0xE4B2  # Replace with your actual Vendor ID in hexadecimal format
    target_pid = 0x0045  # Replace with your actual Product ID in hexadecimal format
    baudrate = 115200
    serial_port, selected_port = initialize_serial_port(baudrate, target_vid, target_pid, logger)

    if serial_port is not None:
        serial_port.write(b'connect\n')
        ack = serial_port.readline().decode('utf-8').strip()
        if ack == 'ready':
            serial_port.write(b'P\n')
            ack = serial_port.readline().decode('utf-8').strip()
            logger("TD1S: Ready to collect data.")

            # Print port parameters
            if selected_port:
                logger(f"Port Parameters - Device: {selected_port.device}, VID: {selected_port.vid}, PID: {selected_port.pid}, Serial Number: {selected_port.serial_number}, Baudrate: {serial_port.baudrate}, Parity: {serial_port.parity}, Stop Bits: {serial_port.stopbits}, Flow Control: {serial_port.rtscts}")
            else:
                logger("No port selected.")

            try:
                while True:
                    # Read data from serial port until newline character is encountered
                    data_str = serial_port.readline().decode('utf-8').strip().split(',')
                    if len(data_str) == 6:
                        logger(data_str)
                        uid, a, b, c, rd, color = data_str
                        return rd, color
            except:
                pass
        return "", ""
    return None, None


if __name__ == "__main__":
    collect_data()
