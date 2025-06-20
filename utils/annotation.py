# -*- coding: utf-8 -*-

# annotation_ui.py

import os
import re
import glob
from datetime import datetime, timedelta
from IPython.display import display, clear_output, Javascript
import ipywidgets as widgets
import pandas as pd
from base64 import b64encode
import configuration as cf
from gspread_dataframe import get_as_dataframe, set_with_dataframe


def labels2color(labels):
    x = labels.get('Classe')

    color = cf.value_to_color.get(x, 'gray')

    return color
    
def assign_colors(data_dict, direction):
    color_map = {}
    for filename, labels in data_dict.items():
        if filename.split('_')[0] == direction:
          timestamp = filename.split('_')[1][:-4]
          color_map[timestamp] = labels2color(labels)
    return color_map

def build_initial_dict_from_images(root_folder='images_to_label'):
    image_data = {}
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.jpg'):
                image_data[filename] = {'Classe': None, 'Nebul': None, 'Hauteur': None}
    return image_data


def get_interpreted_labels(dict_labels, key, correspondance):
    if key is None or key not in dict_labels:
        return "no label"

    labels = dict_labels[key]  # Expected format: {'C': X, 'N': Y, 'H': Z}
    X = labels['Classe']
    return f"{correspondance[int(X)]} (classe {X})" if X in correspondance else f"Pas de labels"




def text2labels(text):
    # Normalize spaces and underscores
    cleaned = re.sub(r'[\s_]+', ' ', text.strip())

    # Match tokens like C45, h1200, etc.
    matches = re.findall(r'\b([cnh])(\d+)\b', cleaned, flags=re.IGNORECASE)

    if not matches:
        return "SVP repecter le format: Cx Ny Hz avec X,Y,Z des entiers positifs"

    label_dict = {}
    key_map = {'c': 'Classe', 'n': 'Nebul', 'h': 'Hauteur'}

    for key, val in matches:
        val = int(val)
        if val < 0:
            return "SVP repecter le format: Cx Ny Hz avec X,Y,Z des entiers positifs"
        if key.lower() == 'n' and val > 8:
            return "La nébulosité (N) doit être un entier entre 1 et 8"
        label_dict[key_map[key.lower()]] = val

    return label_dict
    

def send_labels(dict_labels, filename_to_labels):
    for filename, labels in filename_to_labels.items():
        if isinstance(labels, str):
            return labels  # Return the error immediately
        if filename not in dict_labels:
            return f"l'image n'est pas dans le dictionnaire"
        dict_labels[filename].update(labels)
    return dict_labels

# Manip the google sheet

def update_worksheet(worksheet, data_dict):
    # Step 1: Load sheet into DataFrame (or create empty one if necessary)
    df_sheet = get_as_dataframe(worksheet, dtype=object, header=0).dropna(how='all')

    if df_sheet.empty or all(c is None or str(c).strip() == '' for c in df_sheet.columns):
        df_sheet = pd.DataFrame(columns=['Image'])

    # Step 2: Create DataFrame from dict
    df_new = pd.DataFrame.from_dict(data_dict, orient='index')
    df_new.index.name = 'Image'
    df_new.reset_index(inplace=True)


    # Step 3: Ensure both DataFrames have the same columns
    all_columns = sorted(set(df_sheet.columns).union(df_new.columns))
    df_sheet = df_sheet.set_index('Image').reindex(columns=[col for col in all_columns if col != 'Image'])
    df_new = df_new.set_index('Image').reindex(columns=[col for col in all_columns if col != 'Image'])

    # Step 4: Insert or update rows from df_new into df_sheet
    df_sheet.update(df_new)              # update existing rows
    df_combined = df_sheet.combine_first(df_new)  # add new rows
    df_combined.reset_index(inplace=True)

    # Step 5: Reorder columns alphabetically (with 'Image' always first)
    ordered_columns = ['Image'] + sorted(c for c in df_combined.columns if c != 'Image')
    df_combined = df_combined[ordered_columns]

    # Step 6: Write back to sheet
    worksheet.clear()
    set_with_dataframe(worksheet, df_combined)



def complete_dict_from_worksheet(worksheet, data_dict):
    # Step 1: Load worksheet as DataFrame
    df_sheet = get_as_dataframe(worksheet, dtype=object, header=0).dropna(how='all')
    if df_sheet.empty or 'Image' not in df_sheet.columns:
        return data_dict  # nothing to complete

    df_sheet.set_index('Image', inplace=True)

    # Step 2: For each image in sheet, insert or update in data_dict
    for image_name, row in df_sheet.iterrows():
        row_dict = row.dropna().to_dict()  # skip NaN cells
        if image_name not in data_dict:
            data_dict[image_name] = row_dict
        else:
            for key, val in row_dict.items():
                if data_dict[image_name].get(key) is None:
                    data_dict[image_name][key] = val

    return data_dict


def compare_labels(dict_tuto_labels, filename_to_labels):
    # Extract the single key-value pair from filename_to_labels
    filename, labels = list(filename_to_labels.items())[0]

    # Retrieve the corresponding value from dict_tuto_labels
    tutorial_labels = dict_tuto_labels.get(filename)

    if tutorial_labels is None:
        return "Image non annotée pour le tutoriel."

    # Extract the values to compare (assuming 'Classe' is the key we are interested in)
    N = labels.get('Classe')
    Ny = tutorial_labels.get('Classe')

    if N is None or Ny is None:
        return "Image non annotée pour le tutoriel."

    try:
        # Convert N and Ny to integers
        N = int(N)
        Ny = int(Ny)
    except (ValueError, TypeError):
        return "Image non annotée pour le tutoriel."

    # Compare N and Ny and generate the explanation
    if N != Ny:
        if Ny == 2:
            explanation = "Erreur, attention au Cb !"
        elif Ny - N == 1:
            explanation = "Erreur (?), mais pas loin !"
        elif Ny in [71, 72, 73, 41, 42, 43, 23, 44, 100]:
            explanation = "Attention, classe rare !"
        else:
            explanation = "Erreur (?)"
    else:
        explanation = "Bien vu !"

    # Format the solution and explanation
    choice = f"Classe choisie : c{N}" 
    solution = f"Solution : c{Ny}"
    result = f"{choice} ; {explanation} ; {solution}".strip()

    return result



class AnnotationUI:
    def __init__(self, image_dir, worksheet, direction, mode='tutoriel'):
        self.mode = mode
        self.image_dir = image_dir
        self.worksheet = worksheet
        self.direction = direction
        self.starting_image_idx = 2
        self.correspondance = cf.correspondance
        self.direction2order = {
                                  'E': [3, 2, 1, 4, 0],
                                  'N': [4, 3, 2, 1, 0],  # CGEO, E, N, O, S 
                                  'O': [1, 4, 3, 2, 0], 
                                  'S': [2, 1, 4, 3, 0],  
                               }
        if self.mode == 'tutoriel':
            self.dict_labels = build_initial_dict_from_images(image_dir)
            self.dict_tuto_labels = complete_dict_from_worksheet(worksheet, build_initial_dict_from_images(image_dir))
        else:
            self.dict_labels = complete_dict_from_worksheet(worksheet, build_initial_dict_from_images(image_dir))

        self.subfolders = self._get_subfolders()
        self.color_map = assign_colors(self.dict_labels, direction)

        self.current_subfolder_index = None
        self.current_image_index = self.starting_image_idx
        
        self._build_widgets()
        self._init_callbacks()
        self._build_button_list()
        self._render_initial_view()
        

        


    def _get_subfolders(self):
        return sorted([
            os.path.join(self.image_dir, d)
            for d in os.listdir(self.image_dir)
            if os.path.isdir(os.path.join(self.image_dir, d))
        ])

    def _build_widgets(self):
        display(widgets.HTML("""
        <style>
        .widelabel input {
            width: 100% !important;
            font-size: 16px;
            padding: 6px;
            display: block;
            margin: 0 auto;
        }
        </style>
        """))

        self.button_box = widgets.VBox()
        self.viewer_box = widgets.VBox()
        self.layout_box = widgets.VBox()

        self.image_html = widgets.HTML()
        self.meta_label = widgets.Label()
        self.meta_label2 = widgets.HTML()
        self.meta_label3 = widgets.Label()
        self.status_label = widgets.Label()
        self.result_output = widgets.Output()

        self.label_input = widgets.Text(
            placeholder='Write a label & press Enter',
            layout=widgets.Layout(height='40px', display='none')
        )
        self.label_input.add_class("widelabel")
        self.label_input.add_class("large-placeholder")
        self.label_input.on_submit(self._on_label_submit)

        self.close_button = widgets.Button(
            description='Fermeture pop-up',
            layout=widgets.Layout(width='20%', height='30px', align_self='flex-end'),
            style={'button_color': '#444444', 'font_weight': 'bold', 'text_color': 'white'}
        )
        self.close_button.on_click(self._return_to_buttons)

        self.folder_buttons = []
        self.viewer_box.children = [
                    self.meta_label,
                    self.meta_label3,
                    self.image_html,
                    self.meta_label2,
                    self.status_label,
                    self.label_input,
                    self.result_output,
                    widgets.HBox([self.close_button])
                ]

    def _build_button_list(self):
        for idx, folder in enumerate(self.subfolders):
            folder_name = os.path.basename(folder)
            ts_raw = folder_name.split('_')[0]
            try:
                dt = datetime.strptime(ts_raw, "%Y%m%d%H%M")
                readable_dt = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                readable_dt = "??/??/???? ??:??"

            image_files = sorted([
                f for f in os.listdir(folder)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ])

            try:
                image_files = [image_files[i] for i in self.direction2order[self.direction]]
                third_image_name = image_files[self.starting_image_idx]
            except Exception:
                third_image_name = None

            label_text = get_interpreted_labels(self.dict_labels, third_image_name, self.correspondance)
            full_label = f"{readable_dt}\n{label_text}"

            btn = widgets.Button(
                description=full_label,
                layout=widgets.Layout(width='60%', height='23px'),
                style={
                    'button_color': self.color_map.get(ts_raw, '#dddddd'),
                    'font_weight': 'bold',
                    'text_color': 'black'
                }
            )
            btn._idx = idx
            btn.on_click(self._show_image_view)
            self.folder_buttons.append(btn)

        self.button_box.children = [widgets.VBox(self.folder_buttons)]

    def _render_initial_view(self):
        self.layout_box.children = [self.button_box]
        display(self.layout_box)


    def _show_image_view(self, b):
        self.current_subfolder_index = b._idx
        self.current_image_index = self.starting_image_idx
        self._update_image_display()
        self.layout_box.children = [self.viewer_box]  # switch to viewer
        
    def _return_to_buttons(self, _=None):
        self.layout_box.children = [self.button_box]

    def _on_label_submit(self, change):
        text = change.value.strip()
        if not text:
            return

        with self.result_output:
            clear_output()
            try:
                subfolder = self.subfolders[self.current_subfolder_index]
                images = sorted([
                    f for f in os.listdir(subfolder)
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
                ])

                images = [images[i] for i in self.direction2order[self.direction]]
                image_name = images[self.starting_image_idx]
                labels = text2labels(text)

                if isinstance(labels, str):
                    print(labels)
                else:
                    ts_raw = image_name.split('_')[1][:-4]
                    dt = datetime.strptime(ts_raw, "%Y%m%d%H%M")
                    readable_dt = dt.strftime("%d/%m/%Y %H:%M")
                    filename_to_labels = {image_name: labels}
                    label_text = get_interpreted_labels(filename_to_labels, image_name, self.correspondance)

                    full_label = f"{readable_dt}\n{label_text}"
                    self.folder_buttons[self.current_subfolder_index].description = full_label
                    self.folder_buttons[self.current_subfolder_index].style.button_color = labels2color(labels)

                    # self.dict_labels[image_name].update(labels)
                    # update the dict and the google sheet
                    result = send_labels(self.dict_labels, filename_to_labels)
                    if self.mode == 'tutoriel':
                        comparison_result = compare_labels(self.dict_tuto_labels, filename_to_labels)
                        print(comparison_result)
                    else:
                        update_worksheet(self.worksheet, filename_to_labels)
                        print(f'annotation {label_text} prise en compte')
            except Exception as e:
                print("Error:", e)
        change.value = ''

    def _load_image_html(self, image_path, highlight=False):
        with open(image_path, 'rb') as f:
            encoded = b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1][1:]
        border_style = "border: 5px solid limegreen;" if highlight else "border: none;"
        return f"""
        <style>
        .hover-container {{
          position: relative;
          width: 800px;
          height: auto;
        }}
        .hover-container img {{
          width: 100%;
          height: auto;
          display: block;
          {border_style}
        }}
        .hover-button {{
          position: absolute;
          background: rgba(255,255,255,0.5);
          border: none;
          font-size: 2em;
          padding: 10px;
          display: none;
          cursor: pointer;
          z-index: 10;
        }}
        .hover-container:hover .hover-button {{
          display: block;
        }}
        #left-btn  {{ left: 0; top: 50%; transform: translateY(-50%); }}
        #right-btn {{ right: 0; top: 50%; transform: translateY(-50%); }}
        #up-btn    {{ top: 0; left: 50%; transform: translateX(-50%); }}
        #down-btn  {{ bottom: 0; left: 50%; transform: translateX(-50%); }}
        </style>

        <div class="hover-container">
            <button id="left-btn" class="hover-button" onclick="google.colab.kernel.invokeFunction('notebook.on_left', [], {{}})">‹</button>
            <button id="right-btn" class="hover-button" onclick="google.colab.kernel.invokeFunction('notebook.on_right', [], {{}})">›</button>
            <button id="up-btn" class="hover-button" onclick="google.colab.kernel.invokeFunction('notebook.on_up', [], {{}})">˄</button>
            <button id="down-btn" class="hover-button" onclick="google.colab.kernel.invokeFunction('notebook.on_down', [], {{}})">˅</button>
            <img src="data:image/{ext};base64,{encoded}" />
        </div>
        """

    def _build_meta_table(self, subfolder: str) -> str:
        import pandas as pd

        station_names = {
            "31069001": "Blagnac",
            "31157001": "Francazal"
        }

        # Extract timestamp from folder name
        timestamp_str = os.path.basename(subfolder)
        t0 = datetime.strptime(timestamp_str, "%Y%m%d%H%M")

        # Find TEL_*.csv file
        tel_files = glob.glob(os.path.join(subfolder, "TEL_*.csv"))
        if not tel_files:
            raise FileNotFoundError("No TEL_*.csv file found.")
        tel_path = tel_files[0]

        # Read CSV
        df = pd.read_csv(tel_path, index_col=0)
        df.index = df.index.astype(str)

        # Build header with time labels
        time_labels = df.columns.astype(int)
        time_cells = ""
        for col in time_labels:
            t = t0 + timedelta(minutes=col)
            color = "red" if col == 0 else "black"
            time_cells += f'<th style="color:{color}; font-weight: normal;">{t.strftime("%H:%M")}</th>'

        html = '''
        <table style="
            border-collapse: collapse;
            border: 1px solid black;
            font-family: sans-serif;
            font-size: 12px;
            line-height: 1.2em;
            min-width: 700px;
            transform: scaleX(1.16);
            transform-origin: left;
        ">
        '''

        html += f'''
        <tr>
            <td rowspan="3" style="
                writing-mode: horizontal-tb;
                text-align: center;
                font-weight: bold;
                padding: 4px;
                border: 1px solid black;
            ">Mesures par télémètre</td>
            <th style="border: 1px solid black;">Station</th>{time_cells}
        </tr>
        '''

        def format_cell(val):
            style = "border: 1px solid black; padding: 2px;"
            if pd.isna(val):
                return f'<td style="{style}"></td>'
            try:
                val = float(val)
            except:
                return f'<td style="{style}">{val}</td>'
            if val == 7800:
                color = "lightgrey"
            elif val > 5000:
                color = "blue"
            elif val > 2000:
                color = "orange"
            elif val >= 0:
                color = "darkgreen"
            else:
                color = "black"
            return f'<td style="{style} color:{color};">{int(val)}</td>'

        for station_id in df.index[:2]:
            station_name = station_names.get(station_id, f"Station {station_id}")
            row = f'<tr><td style="border: 1px solid black;">{station_name} ({station_id})</td>'
            row += "".join(format_cell(df.loc[station_id, col]) for col in df.columns)
            row += "</tr>"
            html += row

        html += "</table>"
        return html


    def _update_image_display(self):
        subfolder = self.subfolders[self.current_subfolder_index]
        images = sorted([
            os.path.join(subfolder, f) for f in os.listdir(subfolder)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])


        try:
            images = [images[i] for i in self.direction2order[self.direction]]
        except Exception:
            images = []

        if not images:
            self.image_html.value = "<b>No image</b>"
            self.meta_label.value = f"[{os.path.basename(subfolder)}] — No images"
            self.meta_label2.value = f"[{os.path.basename(subfolder)}] — No metadata"
            self.meta_label3.value = f"[{os.path.basename(subfolder)}] — No value"
            self.status_label.value = ""
            self.label_input.layout.display = 'none'
            return

        self.current_image_index %= len(images)
        image_path = images[self.current_image_index]
        self.image_html.value = self._load_image_html(image_path, highlight=(self.current_image_index == self.starting_image_idx))

        filename = os.path.basename(image_path)
        direction = filename.split('_')[0] if '_' in filename else '?'
        label_text = get_interpreted_labels(self.dict_labels, filename, self.correspondance)
        html = self._build_meta_table(subfolder)

        self.meta_label.value = f"Direction: {direction}"
        self.meta_label2.value = html
        self.meta_label3.value = f"Labels: {label_text}"
        self.status_label.value = f"[{filename} — Image {self.current_image_index + 1}/{len(images)}]"

        if self.current_image_index == self.starting_image_idx:
            self.label_input.layout.display = 'block'
        else:
            self.label_input.layout.display = 'none'

        with self.result_output:
            clear_output()

        display(Javascript('''
        if (!window.simplifiedKeysInitialized) {
          document.addEventListener('keydown', function(event) {
            const tag = document.activeElement.tagName.toLowerCase();
            const isTyping = tag === 'input' || tag === 'textarea';
            if (isTyping) return;
            if (event.key === 'ArrowLeft') {
              google.colab.kernel.invokeFunction('notebook.on_left', [], {});
            } else if (event.key === 'ArrowRight') {
              google.colab.kernel.invokeFunction('notebook.on_right', [], {});
            } else if (event.key === 'a' || event.key === 'A') {
              google.colab.kernel.invokeFunction('notebook.on_up', [], {});
            } else if (event.key === 'z' || event.key === 'Z') {
              google.colab.kernel.invokeFunction('notebook.on_down', [], {});
            }
          });
          window.simplifiedKeysInitialized = true;
        }
        '''))


    def _init_callbacks(self):
        from google.colab import output
        output.register_callback('notebook.on_left', self._on_left)
        output.register_callback('notebook.on_right', self._on_right)
        output.register_callback('notebook.on_up', self._on_up)
        output.register_callback('notebook.on_down', self._on_down)

    def _on_left(self, _=None):
        self.current_image_index -= 1
        self._update_image_display()

    def _on_right(self, _=None):
        self.current_image_index += 1
        self._update_image_display()

    def _on_up(self, _=None):
        self.current_subfolder_index = (self.current_subfolder_index - 1) % len(self.subfolders)
        self.current_image_index = self.starting_image_idx
        self._update_image_display()

    def _on_down(self, _=None):
        self.current_subfolder_index = (self.current_subfolder_index + 1) % len(self.subfolders)
        self.current_image_index = self.starting_image_idx
        self._update_image_display()
