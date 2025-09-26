import datetime
import smtplib
import ssl
from email.message import EmailMessage
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
import subprocess
import shlex

from dotenv import load_dotenv

load_dotenv()


def add_email_in_inbox(sender_name, sender_email, subject, email_body, attachments=None):
    receiver = f"Joseph <{os.environ.get("GMAIL_EMAIL")}>"

    return mail_trap_add_email(email_body, sender_email, sender_name, subject, receiver=receiver, attachments=attachments)

def mail_trap_add_email(email_body, sender_email, sender_name, subject, receiver="User <jseed05@proton.me>",
                        attachments=None):
    """
    Send an email via Mailtrap with optional text file attachments.

    Parameters:
    - email_body: String content of the email
    - sender_email: Original sender email address. Must end with "@aibrilliance.online". Other domains are not supported.
    - sender_name: Name of the sender
    - subject: Email subject
    - receiver: Recipient email address (default: "User <jseed05@proton.me>")
    - attachments: Optional list of dictionaries, each with 'filename' and 'content' keys
                   Example: [{'filename': 'test.txt', 'content': 'This is test content'}]

    Returns:
    - Dictionary with status information
    """
    if not sender_email.endswith("@aibrilliance.online"):
        return {
            "status": "error",
            "message": "Sender email from domain other than @aibrilliance.online is not supported. Sender email must end with @aibrilliance.online. Please try again."
        }
    try:
        sender = f"{sender_name} <{sender_email}>"
        reply_to = f"{sender_name} <{sender_email}>"

        # Create an EmailMessage object for better header handling
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['To'] = receiver
        msg['From'] = sender
        msg['Reply-To'] = reply_to  # Add the Reply-To header

        # Set the content
        msg.set_content(email_body)

        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                if 'filename' in attachment and 'content' in attachment:
                    # Add the attachment with provided content
                    msg.add_attachment(
                        attachment['content'].encode(),
                        filename=attachment['filename'],
                        subtype='plain',
                        maintype='text'
                    )

        with smtplib.SMTP("live.smtp.mailtrap.io", 587) as server:
            server.starttls()
            server.login(os.environ.get("MAILTRAP_USER"), os.environ.get("MAILTRAP_PASSWORD"))
            server.sendmail(sender, receiver, msg.as_string())

        # Create a list of attachment filenames for the response
        attachment_names = [att['filename'] for att in (attachments or [])]

        print("Email sent successfully.")
        date_and_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M %p')
        date = date_and_time.split(" ")[0]
        time = date_and_time.split(" ")[1]
        description = (f"Email from: {sender}\n"
                       f"Date: {date}, Time: {time}\n"
                           f"Subject: {subject}\n"
                           f"Email body: {email_body}\n"
                           f"Attachments: {', '.join(attachment_names) if attachment_names else 'None'}\n"
                           # f"Warning (Important): Added sender has email {new_sender_email}, which may be different from {sender_email} due to tool limitations.\n"
                       )
        return {
            "status": "success",
            "message": f"Email sent with the following details: {description}",
            "description": description
        }
    except Exception as e:
        print(f"Failed to send email: {e}")
        return {
            "status": "error",
            "message": f"Failed to send email: {e}"
        }


def send_email(email_body, subject, receiver_name, receiver_email):
    sender_name = "Joseph"
    sender_email = os.environ.get("GMAIL_EMAIL")
    sender = f"{sender_name} <{sender_email}>"
    receiver = f"{receiver_name} <{receiver_email}>"

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(email_body)
    app_password = os.environ.get("GMAIL_APP_PASSWORD")

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            # Login to account
            smtp.login(sender_email, app_password)

            # Send email
            smtp.send_message(msg)
            return {
                "status": "success",
                "message": "Email sent successfully.",
                "description": f"In SENT:\n"
                               f"Email sent to: {receiver}\n"
                               f"Subject: {subject}\n"
                               f"Email body: {email_body}\n"
            }
    except Exception as e:
        print(f"Failed to send email: {e}")
        return {
            "status": "error",
            "message": f"Failed to send email: {e}"
        }

def wait(time_seconds):
    """Wait for a specified number of seconds."""
    time_seconds = int(time_seconds)
    if time_seconds > 300:
        return {"status": "error", "message": "Wait time exceeds 5 minutes"}

    time.sleep(time_seconds)
    return {"status": "success", "message": f"Waited for {time_seconds} seconds"}


def create_file(filename, content, directory="~/Documents"):
    try:
        # Expand the tilde to the user's home directory
        expanded_directory = os.path.expanduser(directory)

        # Create directory if it doesn't exist
        if not os.path.exists(expanded_directory):
            os.makedirs(expanded_directory)

        # Create full file path
        file_path = os.path.join(expanded_directory, filename)

        # Write content to file
        with open(file_path, 'w') as file:
            file.write(content)
            # No need for explicit flush() or close() when using 'with'

        return {
            "status": "success",
            "message": f"File {filename} created in {expanded_directory}",
            "description": f"{filename} exists in directory {expanded_directory}\n"
                           f"Content: {content}\n"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating file {filename} in directory {expanded_directory}: {str(e)}"
        }


class PersistentTerminal:
    def __init__(self, initial_dir=None):
        """
        Initialize a persistent terminal session with an optional starting directory.
        """
        # Set initial directory to ~/Desktop/oi if not specified
        if initial_dir is None:
            initial_dir = os.path.expanduser("~/Desktop/oi")

        # Create a persistent shell process
        self.shell = subprocess.Popen(
            ['/bin/bash'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=initial_dir,
            bufsize=1
        )

        # Change to the initial directory and clear any welcome messages
        self._execute_raw("cd " + shlex.quote(initial_dir) + "; echo READY")

    def _execute_raw(self, command):
        """
        Execute a command directly in the shell and return output.
        """
        # Send the command to the shell
        self.shell.stdin.write(command + "\n")
        self.shell.stdin.write("echo '___END_OF_COMMAND___'\n")
        self.shell.stdin.flush()

        # Read output until the marker
        output = []
        while True:
            line = self.shell.stdout.readline()
            if '___END_OF_COMMAND___' in line:
                break
            output.append(line)

        return ''.join(output).strip()

    def execute(self, command):
        """
        Run a command on the persistent terminal and return the output.
        """
        try:
            # Execute the command with a marker to identify the end of output
            output = self._execute_raw(command)

            # Get current working directory for information purposes
            pwd_output = self._execute_raw("pwd")

            return {
                "status": "success",
                "message": f"Command executed successfully."
                           f"{f"\nOutput: {output}" if output else ""}"
                           f"\nCurrent directory: {pwd_output}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing command: {str(e)}"
            }

    def close(self):
        """
        Close the persistent terminal process.
        """
        if self.shell:
            self.shell.terminate()
            self.shell = None


# Example usage:
# terminal = PersistentTerminal()  # Create instance that starts at ~/Desktop/oi
# result = terminal.execute("ls -la")  # Run a command
# result = terminal.execute("cd Documents")  # Change directory
# result = terminal.execute("ls -la")  # Run in the new directory
# terminal.close()  # Close when done

# Function that maintains compatibility with your original interface
def ubuntu_terminal(command):
    """
    Run a command on the terminal and return the output.
    Uses a global persistent terminal instance.
    """
    global _persistent_terminal

    # Initialize the terminal if not already done
    if '_persistent_terminal' not in globals() or _persistent_terminal is None:
        _persistent_terminal = PersistentTerminal()

    # Execute the command
    return _persistent_terminal.execute(command)


if __name__ == "__main__":
    add_email_in_inbox("Jusuf", "JusufSeedat@gmail.com", "Test Subject", "This is a test email body.")
