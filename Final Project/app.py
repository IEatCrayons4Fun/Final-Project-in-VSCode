import csv
import json
import os
import re
import shutil
import gradio as gr




# Keywords Section

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
keyword_file = os.path.join(BASE_DIR, "keywords.json")
default_bad_words = ["hurt", "pathetic", "terrible", "miserable", "upset",
								 "attacking", "insulting", "personal", "look down on"]

def save_keywords(keyword):
		with open(keyword_file, "w", encoding="utf-8") as f:
				json.dump(keyword, f, indent=2)

def load_keywords():
		if not os.path.exists(keyword_file):
				return {}
		try:
				with open(keyword_file, encoding="utf-8") as f:
						data = json.load(f)
				if not isinstance(data, dict):
						return {}
				keywords = {}
				for word, score in data.items():
						clean_word = str(word).strip().lower()
						if not clean_word:
								continue
						try:
								keywords[clean_word] = max(1, int(score))
						except (TypeError, ValueError):
								keywords[clean_word] = 1
				return keywords
		except (json.JSONDecodeError, OSError, AttributeError):
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
folder = os.path.join(BASE_DIR, "uploaded_logs")
os.makedirs(folder, exist_ok = True)

def saved_logs():
	try:
		return sorted(
			f for f in os.listdir(folder)
			if f.lower().endswith(('.txt', '.json', '.csv'))
			and os.path.isfile(os.path.join(folder, f))
		)
	except OSError:
		return []

def save_upload(upload):
	if not upload:
		gr.Info("Choose a file to upload first")
		files = saved_logs()
		return gr.Dropdown(choices=files), gr.Dropdown(choices=files)
	name = os.path.basename(upload)
	destination = os.path.join(folder, name)
	try:
		if os.path.abspath(upload) != os.path.abspath(destination):
			shutil.copy2(upload, destination)
		gr.Info(f"Uploaded '{name}'.")
	except (OSError, shutil.Error) as exc:
		gr.Info(f"Could not upload '{name}': {exc}")
	files = saved_logs()
	return (
		gr.Dropdown(choices=files, value=name if name in files else None),
		gr.Dropdown(choices=files),
	)

def remove_file(name, current):
	name = os.path.basename(name or "")
	path = os.path.join(folder, name)
	if not name or not os.path.isfile(path):
		gr.Info("Choose a file to remove first.")
	else:
		try:
			os.remove(path)
			gr.Info(f"Removed '{name}'.")
		except OSError as exc:
			gr.Info(f"Could not remove '{name}': {exc}")
	files = saved_logs()
	keep = current if current in files else None
	return (
		gr.Dropdown(choices=files, value=keep),
		gr.Dropdown(choices=files, value=None),
	)




# Scanning file
def finding_keywords(saved_log):
	if not saved_log:
		gr.Info("Choose a chat log to scan first.")
		return "No chat log selected."

	name = os.path.basename(saved_log)
	path = os.path.join(folder, name)
	if not os.path.isfile(path):
		gr.Info(f"'{name}' is no longer available.")
		return f"Chat log '{name}' could not be found."
	
	try:

		if name.lower().endswith(".json"):
			with open(path, "r", encoding="utf-8") as f:
				data = json.load(f)
			if isinstance(data, list):
				texts = [
					str(row.get("Message", ""))
					for row in data
					if isinstance(row, dict)
				]
			elif isinstance(data, dict):
				texts = [
					str(value)
					for key, value in data.items()
					if key.lower() in ("message", "messages", "text", "content")
				]
				if not texts:
					texts = [str(data)]
			else:
				texts = [str(data)]
			text = "\n".join(texts)


		elif name.lower().endswith(".csv"):
			texts = []
			with open(path, "r", encoding="utf-8", newline="") as f:
				reader = csv.DictReader(f)
				for row in reader:
					message = row.get("Message")
					texts.append(str(message) if message is not None else "")
			text = "\n".join(texts)

			
		else:
			with open(path, "r", encoding="utf-8") as f:
				text = f.read()
	except (OSError, json.JSONDecodeError, UnicodeDecodeError, csv.Error) as exc:
		gr.Info(f"Could not scan '{name}': {exc}")
		return f"Could not scan '{name}'."

	keywords = load_keywords()
	if not keywords:
		gr.Info("The keyword list is empty.")
		return "No keywords configured."

	matches = []
	for keyword, score in sorted(keywords.items()):
		pattern = re.compile(re.escape(keyword), re.IGNORECASE)
		count = len(pattern.findall(text))
		if count:
			matches.append(f"{keyword}: {count} occurrence{'s' if count != 1 else ''}, score {score}")

	if not matches:
		return f"No keywords found in '{name}'."
	return f"Keyword scan results for '{name}':\n" + "\n".join(matches) + f"\n\nKeywords found: {len(matches)}"



# Plain Printing whats in the chatlogs
#Json loading function
def load_json_messages(path):
	with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
	messages = []
	for row in data:
		if not isinstance(row, dict):
			continue
		messages.append({"time" : row.get("Time", ""),
										 "user" : row.get("User", ""),
										 "message" : row.get("Message", "")})
	return messages



# .cvc loading function
def load_csv_messages(path):
	messages = []
	with open(path, "r", encoding="utf-8", newline=" ") as f:
		reader = csv.DictReader(f)
		for row in reader:
			messages.append({"time" : row.get("Time", ""), "user" : row.get("User", ""), "message" : row.get("Message", "")})
	return messages


# .txt loading function
def load_txt_messages(path):
	messages = []
	with open(path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line.startswith("["):
				continue
			end = line.index("]")
			time = line[1:end].strip()
			rest = line[end+1:].strip()
			messages.append({"time" : time,"user" : "", "message" : rest})
	return messages

# Loading all file types
def load_messages(path):
	path = os.path.join(folder, path)
	if not os.path.isfile(path):
		return None
	lower_path = path.lower()
	if lower_path.endswith(".json"):
		return load_json_messages(path)
	elif lower_path.endswith(".csv"):
		return load_csv_messages(path)
	elif lower_path.endswith(".txt"):
		return load_txt_messages(path)
	else:
		return None


# displaying the messages in the UI
def show_raw_messages(name):
	if not name:
		return []
	messages = load_messages(name)
	if messages is None:
		gr.Info("Could not load chat file.")
		return []
	return [[i.get("time", ""), i.get("user", ""), i.get("message", "")] for i in messages]



			











# refresh dropdown
def refresh_dropdown():
	files = saved_logs()
	return gr.Dropdown(choices=files), gr.Dropdown(choices = files)



# Gradio Setup


 #try:
		#demo.close() # type: ignore
#except NameError:
		#pass


# Keyword UI Functions
def ui_add(word, score):
	if word in add_keyword(word, score):
		gr.Info("Updated Score", duration=2.5)
	else:
		gr.Info(add_keyword(word, score))
		
	return keyword_rows(), gr.Dropdown(choices=sorted(load_keywords()), value=None)

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
			log_remove = gr.Dropdown(choices=saved_logs(), label="File to remove", scale=2)
			log_remove_btn = gr.Button("Remove file", variant="primary", scale=2)



# Different Tabs
	with gr.Accordion("Additional Options", open = False):
		with gr.Tab("Keywords"):
			with gr.Row():
				with gr.Column(): 
					keyword_table = gr.Dataframe(value=keyword_rows(), headers=["Keyword", "Initial score"], interactive=False, label="Current keywords")
				with gr.Column(): 
					new_word = gr.Textbox(label="New keyword or phrase / Update keyword", placeholder="Type in a keyword")
					new_score = gr.Number(label="Initial score", value=1, precision=0, minimum=1)
					add_button = gr.Button("Add / Update keyword", variant="primary")
					remove_dropdown = gr.Dropdown(choices=sorted(load_keywords()), label="Keyword to remove")
					remove_button = gr.Button("Remove keyword", variant='primary')

					add_button.click(ui_add, [new_word, new_score], [keyword_table, remove_dropdown])
					remove_button.click(ui_remove, remove_dropdown, [keyword_table, remove_dropdown])

		with gr.Tab("Scan"):
			gr.Markdown("### Scan a chat log for keywords")
			with gr.Row():
				with gr.Column():
					log_dropdown = gr.Dropdown(choices=saved_logs(), label="Saved logs (pick one)")
					scan_button = gr.Button("Scan for keywords", variant = "primary")
				with gr.Column():
					scan_output = gr.Textbox(label="Scan results", interactive=False, placeholder="Scan results will appear here")

			#Button Function
			scan_button.click(finding_keywords, [log_dropdown], [scan_output])

		upload_box.upload(save_upload, upload_box, [log_dropdown, log_remove])
		log_remove_btn.click(remove_file, [log_remove, log_dropdown], [log_dropdown, log_remove])
		demo.load(refresh_dropdown, None, [log_dropdown, log_remove])


demo.launch(theme=gr.Theme.from_hub("CultriX/gradio-theme"))