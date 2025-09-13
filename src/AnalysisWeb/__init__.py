import os
import glob
from pathlib import Path
from datetime import datetime
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

now = datetime.now()
formatted_time = now.strftime("%Y%m%d_%H_%M_%S")

current_dir = os.getcwd()

# 3. Join the safe, formatted string
_DEFAULT_SAVE_DIR = os.path.join(current_dir, formatted_time)


def set_default_save_dir(file_loc):
    "To set the default save_dir"
    global _DEFAULT_SAVE_DIR
    if os.path.exists(file_loc):
        _DEFAULT_SAVE_DIR = file_loc


def get_default_save_dir():
    "To get the default save_dir"
    return _DEFAULT_SAVE_DIR


def create_results_index(
    directory=_DEFAULT_SAVE_DIR, title="ML Analysis Results Index", file_groups={}
):
    """Creates an HTML index page linking to all result files."""
    output_file = ("index.html",)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    # Find all HTML files in the directory
    html_files = glob.glob(os.path.join(directory, "*.html"))

    # Filter out the index file itself if it exists
    html_files = [f for f in html_files if not f.endswith(output_file)]

    # Group files by their base name pattern

    for file_path in html_files:
        file_name = os.path.basename(file_path)
        # Extract the base name (without test/holdout and extension)
        keys = file_groups.keys()
        key = (file_name.split("_")[-1]).split(".")[0]
        if key in keys:
            file_groups[key][file_name] = file_name
        else:
            if "misc" not in file_groups:
                file_groups["misc"] = {}
            file_groups["misc"][file_name] = file_name

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <a href="/" class="home-button"> 🏠 Home</a>
    <div class="index-container">
        <div class="header">
            <h1>{title}</h1>
            <p>Complete overview of all generated analysis reports</p>
        </div>
        
        <div class="stats">
            <strong>Total Files:</strong> {len(html_files)} | 
            <strong>Groups:</strong> {len(file_groups)} | 
            <strong>Generated:</strong> {Path(output_file).stem}
        </div>
"""

    # NLL Results Section
    html_content += """
        <div class="category">
            <h2 class="category-title">NLL Results</h2>
            <div class="files-grid">
    """

    for group_name in file_groups.keys():

        html_content += """
            <div class="category">
                <h2 class="category-title">Density Ratios</h2>
                <div class="files-grid">
        """

        for file_name in file_groups[group_name].values():
            title = (
                file_name.replace(f"_{group_name}.html", "").replace("_", " ").title()
            )
            html_content += f"""
                    <div class="file-group">
                        <a href="{file_name}" class="file-link">
                            {title} Density Ratios
                            <span class="file-type">({file_name})</span>
                        </a>
                    </div>
            """

        html_content += """
                </div>
            </div>
        """

    # JavaScript for comparison functionality
    html_content += """
        <script>
        function openComparison(file1, file2) {
            // Open both files in new tabs for comparison
            window.open(file1, '_blank');
            window.open(file2, '_blank');
        }
        </script>
    </body>
    </html>
    """
    output_file_path = os.path.join(directory, output_file)
    # Write to file
    with open(output_file_path, "w") as f:
        f.write(html_content)

    print(f"Index created: {output_file_path}")
    print(f"Total files indexed: {len(html_files)}")


def config_to_html(config, filename="config_report.html"):
    """Creates an HTML report of the configuration object with compact layout."""

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <a href="index.html" class="home-button"> 🏠 Home</a>
    <div class="config-container">
        <div class="header">
            <h1>Model Configuration</h1>
        </div>
"""

    # Simple attributes section - now in a grid
    html_content += """
        <div class="section">
            <h2 class="section-title">Basic Configuration</h2>
            <div class="attr-grid">
    """

    list_attrs = []
    simple_attrs = []  # Just attribute names
    dict_attrs = {}

    for attr_name, attr_value in vars(config).items():
        if attr_name in config.exclude_list:
            continue
        if isinstance(attr_value, list):
            list_attrs.append((attr_name, attr_value))
        elif isinstance(attr_value, dict):
            dict_attrs[attr_name] = attr_name
        else:
            simple_attrs.append(attr_name)  # Store only the name

    # Then use getattr() as in your original code
    for attr_name in simple_attrs:
        value = getattr(config, attr_name, "N/A")
        html_content += f"""
                <div class="attr-item">
                    <div class="attr-name">{attr_name}</div>
                    <div class="attr-value">{value}</div>
                </div>
        """

    html_content += """
            </div>
        </div>
    """

    # Lists section - with wrapped columns
    html_content += """
        <div class="section">
            <h2 class="section-title">Lists</h2>
    """

    for attr_name, attr_value in list_attrs:

        html_content += f"""
            <div class="attr-item">
                <div class="attr-name">{attr_name}</div>
                <div class="attr-value">
                    <div class="compact-list">
        """

        # Display items in a compact scrollable list
        for i, item in enumerate(attr_value):
            html_content += f"<pre>{item}</pre>"
            if i >= 20:  # Limit display to 20 items with ellipsis
                html_content += f"<pre>... and {len(attr_value) - 20} more</pre>"
                break

        html_content += f"""
                    </div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
                        Total items: {len(attr_value)}
                    </div>
                </div>
            </div>
        """

    html_content += """
        </div>
    """

    # Dictionaries section - compact display
    html_content += """
        <div class="section">
            <h2 class="section-title">Dictionaries</h2>
            <div class="attr-grid">
    """

    for attr, display_name in dict_attrs.items():
        dictionary = getattr(config, attr, {})
        html_content += f"""
                <div class="attr-item">
                    <div class="attr-name">{display_name}</div>
                    <div class="attr-value">
        """

        if dictionary:
            html_content += """
                        <div class="scrollable">
                            <div class="dict-compact">
            """

            for key, value in dictionary.items():
                html_content += f"""
                                    <div class="dict-item-compact">
                                        <span class="dict-key-compact">{key}:</span>
                                        <span>{value}</span>
                                    </div>
                """
            html_content += f"""
                            </div>
                            <div style="font-size: 0.8em; color: #666; margin-top: 8px;">
                                Total entries: {len(dictionary)}
                            </div>
                        </div>
            """
        else:
            html_content += "Empty dictionary"

        html_content += """
                    </div>
                </div>
        """

    html_content += """
            </div>
        </div>
    </div>
</body>
</html>
"""

    # Write to file
    with open(filename, "w") as f:
        f.write(html_content)


def image_report_to_html(
    base64_image, info_dict, title="Analysis Results", filename="image_report.html"
):
    """Creates an HTML report with a base64 image and dictionary information."""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <a href="index.html" class="home-button"> 🏠 Home</a>
    <div class="report-container">
        <div class="header">
            <h1>{title}</h1>
        </div>
        
        <div class="content-grid">
            <!-- Image Section -->
            <div class="image-section">
                <h2 class="section-title">Visualization</h2>
                <img src="data:image/png;base64,{base64_image}" alt="Analysis Plot" class="plot-image">
            </div>
            
            <!-- Information Section -->
            <div class="info-section">
                <h2 class="section-title">Results Summary</h2>
                <div class="info-grid">
"""

    # Add dictionary items to the info grid
    for key, value in info_dict.items():
        # Determine value type for styling
        value_type = "value-other"
        if isinstance(value, (int, float)):
            value_type = "value-number"
        elif isinstance(value, str):
            value_type = "value-string"
        elif isinstance(value, bool):
            value_type = "value-bool"

        html_content += f"""
                    <div class="info-item">
                        <div class="info-key">{key}</div>
                        <div class="info-value {value_type}">{value}</div>
                    </div>
        """

    html_content += """
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

    # Write to file
    with open(filename, "w") as f:
        f.write(html_content)

    return filename


def save_table_html(df, title, filename):
    """Saves a DataFrame as an HTML file using template markers for clean appending."""

    # Generate table HTML
    table_html = df.to_html(
        index=False, border=0, justify="center", classes="dataframe"
    )

    # Create the new table section
    new_section = f"""
        <div class="section">
            <a href="index.html" class="home-button"> 🏠 Home</a>
            <div class="center">
                <h2>{title}</h2>
                {table_html}
            </div>
        </div>
    """

    if os.path.exists(filename):
        try:
            # Read existing content
            with open(filename, "r") as f:
                content = f.read()

            # Insert new section before the content end marker
            if "<!-- CONTENT_END -->" in content:
                content = content.replace(
                    "<!-- CONTENT_END -->",
                    new_section + "\n        <!-- CONTENT_END -->",
                )
                with open(filename, "w") as f:
                    f.write(content)
            else:
                # File exists but doesn't have our markers, recreate it
                raise ValueError("Invalid file format")

        except (ValueError, Exception):
            full_html = f"""<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <a href="index.html" class="home-button"> 🏠 Home</a>
    <div class="table-container">
        <div class="header">
            <h1>Dataset Analysis Report</h1>
            <p>Comprehensive analysis of all datasets</p>
        </div>
        <!-- CONTENT_START -->
        {new_section}
        <!-- CONTENT_END -->
        <div class="timestamp">
            Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>"""
            with open(filename, "w") as f:
                f.write(full_html)
    else:
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <a href="index.html" class="home-button"> 🏠 Home</a>
    <div class="table-container">
        <div class="header">
            <h1>Dataset Analysis Report</h1>
            <p>Comprehensive analysis of all datasets</p>
        </div>
        <!-- CONTENT_START -->
        {new_section}
        <!-- CONTENT_END -->
        <div class="timestamp">
            Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>"""
        with open(filename, "w") as f:
            f.write(full_html)


def image_gallery_to_html(
    images_data,
    titles=None,
    directory=_DEFAULT_SAVE_DIR,
    output_file="image_gallery.html",
    file_title="Image Gallery",
):
    """
    Create an HTML page with multiple base64 images in a gallery layout.

    Args:
        images_data: List of base64 encoded image strings OR BytesIO objects
        titles: List of titles for each image (optional)
        output_file: Output HTML filename
    """
    from datetime import datetime
    import base64

    if titles is None:
        titles = [f"Image {i+1}" for i in range(len(images_data))]

    # Build image cards
    image_cards = []
    for i, (image_data, title) in enumerate(zip(images_data, titles)):
        # Handle both base64 strings and BytesIO objects
        if hasattr(image_data, "getvalue"):  # It's a BytesIO object
            # Convert BytesIO to base64 string
            image_data.seek(0)  # Reset position to start
            image_base64 = base64.b64encode(image_data.getvalue()).decode("utf-8")
        else:
            # Assume it's already base64 string
            image_base64 = image_data

        image_card = f"""
        <div class="image-card">
            <div class="image-wrapper">
                <img src="data:image/png;base64,{image_base64}" 
                     alt="{title}" 
                     class="gallery-image">
            </div>
            <div class="image-caption">
                <div class="image-title">{title}</div>
                <div class="image-meta">Image {i+1} of {len(images_data)}</div>
            </div>
        </div>
        """
        image_cards.append(image_card)

    # Combine all image cards
    gallery_html = f"""
    <div class="gallery-container">
        {"".join(image_cards)}
    </div>
    """

    # Create complete HTML
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/style.css">
    <title>{file_title}</title>
</head>
<body>
    <a href="index.html" class="home-button"> 🏠 Home</a>
    <div class="table-container">
        <div class="header">
            <h1>Image Gallery</h1>
            <p>Total images: {len(images_data)}</p>
        </div>
        {gallery_html}
        <div class="timestamp">
            Gallery generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>"""

    # Write to file
    with open(output_file, "w") as f:
        f.write(full_html)

    return output_file


class Sequencer:
    """
    The `Sequencer` Class which helps maintain the CSV file system required
    for the index page. For each process (eg. "fit", "valid", "analysis" ...)
    set the result as a string (eg. "Fitting") use the Sequencer to connect
    between the processes and update the status.
    """

    def __init__(self, plots_data_file, date, model_type="", jobID=-1, plots_dir=None):

        self.entry_dict = {
            "date": date,
            "job_id": jobID,
            "type": model_type,
            "Status": "Launched",
            "score": "-",
            "link": "/",
        }

        try:
            self.index_df = pd.read_csv(plots_data_file)
        except FileNotFoundError:
            self.index_df = pd.DataFrame(
                columns=[
                    "date",
                    "type",
                    "job_id",
                    "Status",
                    "score",
                    "link",
                ]
            )

            self.plots_data_file = plots_data_file
            self.next_index = len(self.index_df)
            self.index_df.loc[self.next_index] = self.entry_dict
            self.index_df.to_csv(self.plots_data_file, index=False)
            return

        self.plots_data_file = plots_data_file

        matches = self.index_df.index[self.index_df["date"] == date]

        if not matches.empty:
            # Take the first matching index (or use [-1] for the last match)
            self.next_index = matches[0]
            self.entry_dict = self.index_df.loc[self.next_index].to_dict()

        else:
            # No match → append to the end
            self.next_index = len(self.index_df)
        if plots_dir is not None:
            self.entry_dict["link"] = os.path.basename(plots_dir) + "/index.html"
            self.plots_dir = plots_dir
            create_results_index(self.plots_dir, title=os.path.basename(self.plots_dir))
        else:
            self.entry_dict["link"] = "/"

        self.index_df.loc[self.next_index] = self.entry_dict
        self.index_df.to_csv(self.plots_data_file, index=False)

    def __update__(self, status="Failed"):
        """To update the status and save the df to csv"""
        self.entry_dict["Status"] = status
        try:
            self.index_df.loc[self.next_index] = self.entry_dict
            self.index_df.to_csv(self.plots_data_file, index=False)
            create_results_index(self.plots_dir, title=os.path.basename(self.plots_dir))
        except Exception as save_error:
            print(f"Failed to save results: {save_error}")

    def add_algorithm(self, alg, **kwargs):
        """Run and record the status of an algorythm"""
        try:
            status = alg(**kwargs)  # Pass all keyword arguments to the algorithm

        except Exception as e:
            print(f"Error during {alg.__name__}: {e}")
            status = "Failed"

            raise

        finally:
            self.__update__(status)

    def add_score(self, tag, score):
        """Update score"""
        self.entry_dict[tag] = score
        self.__update__("Scoring...")

    def start(self):
        """Set status to start"""
        self.__update__("Running")

    def end(self):
        """Set status to end"""
        self.__update__("Completed")

    def cancel(self):
        """Set status to calcelled"""
        self.__update__("Cancelled")
