"""
Configuration management for the eranest package.
"""

import os
import sys


def check_cdsapi_config() -> bool:
    """
    Check if CDS API configuration exists and is valid.
    Returns True if configuration exists and is valid, False otherwise.
    """
    cds_file = os.path.expanduser("~/.cdsapirc")
    if not os.path.exists(cds_file):
        return False

    try:
        with open(cds_file, "r") as f:
            content = f.read().strip()
            if not content:
                return False

            # Check for both formats: "url: X\nkey: Y" and "X:Y"
            lines = content.split("\n")
            if len(lines) >= 2:
                # Multi-line format
                url_line = next(
                    (line for line in lines if line.strip().startswith("url:")), None
                )
                key_line = next(
                    (line for line in lines if line.strip().startswith("key:")), None
                )
                if url_line and key_line:
                    url = url_line.split(":", 1)[1].strip()
                    key = key_line.split(":", 1)[1].strip()
                    return bool(url and key)
            elif ":" in content:
                # Single-line format
                url, key = content.split(":", 1)
                return bool(url.strip() and key.strip())

        return False
    except Exception:
        return False


def _create_config_file(api_key: str) -> None:
    """Create the CDS API configuration file."""
    config_path = os.path.expanduser("~/.cdsapirc")
    config_content = f"url: https://cds.climate.copernicus.eu/api/\nkey: {api_key}"

    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"✓ Configuration file created at: {config_path}")
        print("You can now use the CDS API!")
    except Exception as e:
        raise RuntimeError(f"Failed to create configuration file: {e}")


def _is_notebook_environment() -> bool:
    """Check if running in a Jupyter notebook environment."""
    try:
        get_ipython()
        return True
    except NameError:
        return False


def _setup_notebook_widget():
    """Setup interactive widget for notebook environment."""
    try:
        import ipywidgets as widgets
        from IPython.display import HTML, display
    except ImportError:
        return None

    # Create widgets with better paste support
    api_key_widget = widgets.Textarea(
        description="API Key:",
        placeholder="Paste your CDS API key here (Ctrl+V or Cmd+V)",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="80%", height="60px"),
        rows=2,
    )

    submit_button = widgets.Button(
        description="Submit", button_style="success", layout=widgets.Layout(width="20%")
    )

    # Add a clipboard button as backup
    clipboard_button = widgets.Button(
        description="Try Clipboard",
        button_style="info",
        layout=widgets.Layout(width="20%"),
        tooltip="Click to try reading from clipboard",
    )

    output = widgets.Output()

    # Track completion state
    completion_state = {"completed": False, "error": None}

    def on_submit_clicked(b):
        with output:
            output.clear_output()
            print("Submit button clicked! Processing...")

            api_key = api_key_widget.value.strip()
            print(f"API key length: {len(api_key)}")

            if not api_key:
                print("Error: No API key provided")
                completion_state["error"] = "No API key provided"
                return

            try:
                print("Creating configuration file...")
                _create_config_file(api_key)
                completion_state["completed"] = True
                print("✓ Setup completed successfully!")
            except Exception as e:
                error_msg = f"Error: {e}"
                print(error_msg)
                completion_state["error"] = str(e)

    def on_clipboard_clicked(b):
        with output:
            output.clear_output()
            print("Clipboard button clicked! Checking clipboard...")

            clipboard_key = _get_api_key_from_clipboard()
            if clipboard_key:
                api_key_widget.value = clipboard_key
                print(f"✓ Found API key in clipboard: {clipboard_key[:10]}...")
                print("Now click Submit to continue.")
            else:
                print("No valid API key found in clipboard.")
                print(
                    "Please copy your API key and try again, or type it manually in the text area above."
                )

    submit_button.on_click(on_submit_clicked)
    clipboard_button.on_click(on_clipboard_clicked)

    # Add some helpful HTML instructions
    instructions_html = """
    <div style="background-color: #f0f8ff; padding: 10px; border-radius: 5px; margin: 10px 0;">
    <strong>Pasting Help:</strong><br>
    • Try using <kbd>Ctrl+V</kbd> (Windows/Linux) or <kbd>Cmd+V</kbd> (Mac) in the text area<br>
    • If pasting doesn't work, click "Try Clipboard" to read from clipboard automatically<br>
    • You can also type the API key manually<br>
    • The API key should be a long string with letters, numbers, and dashes
    </div>
    """

    display(HTML(instructions_html))

    # Display the widgets
    display(
        widgets.VBox(
            [api_key_widget, widgets.HBox([submit_button, clipboard_button]), output]
        )
    )

    return completion_state


def _get_api_key_from_clipboard():
    """Try to get API key from clipboard."""
    try:
        import pyperclip

        clipboard_content = pyperclip.paste().strip()

        # Basic validation - CDS API keys are typically long strings
        if len(clipboard_content) > 20 and "-" in clipboard_content:
            return clipboard_content
    except (ImportError, Exception):
        pass
    return None


def setup_cdsapi_config():
    """Interactive setup of CDS API configuration."""
    print("\n=== CDS API Configuration Setup ===")
    print("This will create a .cdsapirc file in your home directory.")
    print(
        "You need a CDS account and API key from: https://cds.climate.copernicus.eu/profile"
    )

    is_notebook = _is_notebook_environment()

    if is_notebook:
        print("\nRunning in Jupyter notebook environment.")
        print("Please follow these steps:")
        print("1. Go to https://cds.climate.copernicus.eu/profile")
        print("2. Log in to your account")
        print("3. Click on your username in the top right")
        print("4. Click on 'My API Key'")
        print("5. Copy your API key (the long string after the colon)")
        print("\nThen paste your API key below:")

        # Try widget approach first
        completion_state = _setup_notebook_widget()

        if completion_state is None:
            # Fallback to input() if widgets not available
            print("\nNote: Interactive widgets not available. Using text input.")
            api_key = input("Enter your CDS API key: ").strip()
            if not api_key:
                raise ValueError("No API key provided")
            _create_config_file(api_key)
        else:
            # Instead of waiting with a loop, give user instructions
            print("\n" + "=" * 50)
            print("IMPORTANT: Complete the setup above, then run the next cell:")
            print("=" * 50)
            print()

            # Create a completion check function they can call
            def check_setup_completion():
                if completion_state["completed"]:
                    print("✅ Setup completed successfully!")
                    return True
                elif completion_state["error"]:
                    print(f"❌ Setup failed: {completion_state['error']}")
                    return False
                else:
                    print(
                        "⏳ Setup not completed yet. Please fill in your API key and click Submit above."
                    )
                    return False

            # Make the function globally available
            import __main__

            __main__.check_setup_completion = check_setup_completion

            print("After completing the form above, run: check_setup_completion()")
            print("Or simply continue - the configuration will be checked when needed.")

            # Don't wait here - let the user continue
            return

    else:
        # Command line environment
        print("\nPlease follow these steps:")
        print("1. Go to https://cds.climate.copernicus.eu/user")
        print("2. Log in to your account")
        print("3. Click on your username in the top right")
        print("4. Click on 'My API Key'")
        print("5. Copy your API key (the long string after the colon)")

        # Try clipboard first
        clipboard_key = _get_api_key_from_clipboard()
        if clipboard_key:
            print(f"\nFound potential API key in clipboard: {clipboard_key[:10]}...")
            try:
                response = input("Use this key? (y/n): ").lower().strip()
                if response.startswith("y"):
                    api_key = clipboard_key
                else:
                    api_key = input("Enter your CDS API key: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSetup cancelled.")
                return
        else:
            try:
                api_key = input("\nEnter your CDS API key: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSetup cancelled.")
                return

        if not api_key:
            raise ValueError("No API key provided")

        _create_config_file(api_key)


def ensure_cdsapi_config():
    """
    Ensure CDS API configuration exists and is valid.
    If not, guide the user through setting it up.
    """
    if not check_cdsapi_config():
        try:
            setup_cdsapi_config()

            # Verify the configuration was created successfully
            if not check_cdsapi_config():
                raise RuntimeError(
                    "Configuration file was created but appears to be invalid"
                )

        except (KeyboardInterrupt, EOFError):
            print("\nSetup cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\nError setting up CDS API configuration: {e}")
            print("\nYou can manually create the configuration file:")
            print("1. Create a file named '.cdsapirc' in your home directory")
            print("2. Add these two lines:")
            print("   url: https://cds.climate.copernicus.eu/api")
            print("   key: YOUR_API_KEY_HERE")
            sys.exit(1)
    else:
        print("✓ CDS API configuration is already set up and valid.")
