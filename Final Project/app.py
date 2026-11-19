import os, json, re, shutil, gradio as gr




# Keywords Section

keyword_file = "keywords.json"
default_bad_words = ["hurt", "pathetic", "terrible", "miserable", "upset",
                 "attacking", "insulting", "personal", "look down on"]

def save_keywords(keyword):
    with open(keyword_file, "w") as f:
        json.dump(keyword, f, indent=2)

def load_keywords():
    if not os.path.exists(keyword_file):
        return {}
    try:
        with open(keyword_file) as f:
            data = json.load(f)
        return {str(k).strip().lower(): max(1, int(v)) for k, v in data.items() if str(k).strip()}
    except (json.JSONDecodeError, ValueError, AttributeError):
        return {}

def add_keyword(word, score=1):
    word = (word or "").strip().lower()
    if not word:
        return "Please type a keyword first."
    try:
        score = max(1, int(score))
    except (TypeError, ValueError):
        score = 1
    keyword = load_keywords()
    verb = "Updated" if word in keyword else "Added"
    keyword[word] = score
    save_keywords(keyword)
    return f"{verb} '{word}' (initial score {score})."

def remove_keyword(word):
    word = (word or "").strip().lower()
    keyword = load_keywords()
    if word not in keyword:
        return f"'{word}' is not in the keyword list."
    del keyword[word]
    save_keywords(keyword)
    return f"Removed '{word}'."

def keyword_rows():
    return [[w, s] for w, s in sorted(load_keywords().items())]

def ensure_defaults():
    keyword = load_keywords()
    for i in default_bad_words:
        if i not in keyword:
            keyword[i] = 1
    save_keywords(keyword)

ensure_defaults()



# Chat Log Uploading
folder = "uploaded_logs"
os.makedirs(folder, exist_ok = True)

def saved_logs():
  return sorted(f for f in os.listdir(folder) if f.lower().endswith(('.txt', '.json', '.csv')))

def save_upload(upload):
  if not upload:
    gr.Info("Choose a file to upload first")
    return gr.Dropdown(choices=saved_logs()), gr.Dropdown(choices=saved_logs())
  name = os.path.basename(upload)
  shutil.copy2(upload, os.path.join(folder, name))
  return gr.Dropdown(choices=saved_logs(), value=name), gr.Dropdown(choices=saved_logs())

def remove_file(name, current):
  name = os.path.basename(name or "")
  path = os.path.join(folder, name)
  if not name or not os.path.isfile(path):
    gr.Info("Choose a file to remove first.")
  else:
      os.remove(path)
      gr.Info(f"Removed '{name}'.")
  files = saved_logs()
  keep = current if current in files else None
  return gr.Dropdown(choices=files, value=keep), gr.Dropdown(choices=files, value=None)


# Scanning file

def finding_keywords():
  with open(keyword_file, "r") as f:
    keywords = json.load(f)
  return re.findall('|'.join(keywords.keys()), 'You are bad person')

print(finding_keywords)


try:
    demo.close() # type: ignore
except NameError:
    pass


# Keyword UI Functions
def ui_add(word, score):
    gr.Info(add_keyword(word, score))
    return keyword_rows(), gr.Dropdown(choices=sorted(load_keywords()), value=None), ""

def ui_remove(word):
    gr.Info(remove_keyword(word))
    return keyword_rows(), gr.Dropdown(choices=sorted(load_keywords()), value=None)


# Main UI
with gr.Blocks(title="Chat Sentinel") as demo:
    gr.Markdown("# Chat Sentinel")


# File Uplaoding UI
    with gr.Row():
      with gr.Column():
        upload_box = gr.File(label="Upload a chat log (.txt, .json, .csv)", type="filepath", file_types=[".txt", ".json", ".csv"], height = 150)

      with gr.Column():
          log_remove_dd = gr.Dropdown(choices=saved_logs(), label="File to remove", scale=2)
          log_remove_btn = gr.Button("Remove file", variant="stop", scale=2)

    log_dd = gr.Dropdown(choices=saved_logs(), label="Saved logs (pick one)")
    upload_box.upload(save_upload, upload_box, [log_dd, log_remove_dd])
    log_remove_btn.click(remove_file, [log_remove_dd, log_dd], [log_dd, log_remove_dd])


# Different Tabs
    with gr.Accordion("Additional Options", open = False):
      with gr.Tab("Keywords"):
          kw_table = gr.Dataframe(value=keyword_rows(), headers=["Keyword", "Initial score"],
                                  interactive=False, label="Current keywords")
          with gr.Row():
              new_word = gr.Textbox(label="New keyword or phrase", placeholder="Type in a filter keyword")
              new_score = gr.Number(label="Initial score", value=1, precision=0, minimum=1)
          add_button = gr.Button("Add / update keyword", variant="primary")
          remove_dd = gr.Dropdown(choices=sorted(load_keywords()), label="Keyword to remove")
          remove_button = gr.Button("Remove keyword")

          add_button.click(ui_add, [new_word, new_score], [kw_table, remove_dd, new_word])
          remove_button.click(ui_remove, remove_dd, [kw_table, remove_dd])



demo.launch(theme=gr.Theme.from_hub("CultriX/gradio-theme"))