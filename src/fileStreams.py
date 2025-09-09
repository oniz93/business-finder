import traceback
from typing import BinaryIO, Iterator, Optional
try:
	import orjson as json
except ImportError:
	import json
	print("Recommended to install 'orjson' for faster JSON parsing")

import zstandard

try:
	from zst_blocks_format.python_cli.ZstBlocksFile import ZstBlocksFile
except ImportError:
	pass

def getZstFileJsonStream(f: BinaryIO, chunk_size=1024*1024*10, max_items: Optional[int] = None) -> Iterator[dict]:
	decompressor = zstandard.ZstdDecompressor(max_window_size=2**31)
	currentString = ""
	items_yielded = 0 # Counter for items yielded

	def yieldLinesJson():
		nonlocal currentString, items_yielded
		lines = currentString.split("\n")
		currentString = lines[-1]
		for line in lines[:-1]:
			if max_items is not None and items_yielded >= max_items:
				return # Stop yielding if max_items is reached

			try:
				yield json.loads(line)
				items_yielded += 1
			except json.JSONDecodeError:
				print("Error parsing line: " + line)
				traceback.print_exc()
				continue
	
	zstReader = decompressor.stream_reader(f)
	while True:
		if max_items is not None and items_yielded >= max_items:
			break # Stop reading chunks if max_items is reached

		try:
			chunk = zstReader.read(chunk_size)
		except zstandard.ZstdError:
			print("Error reading zst chunk")
			traceback.print_exc()
			break
		if not chunk:
			break
		currentString += chunk.decode("utf-8", "replace")
		
		yield from yieldLinesJson()
	
	# Yield any remaining lines after the loop, respecting max_items
	if max_items is None or items_yielded < max_items:
		yield from yieldLinesJson()
	
	if len(currentString) > 0 and (max_items is None or items_yielded < max_items):
		try:
			yield json.loads(currentString)
			items_yielded += 1
		except json.JSONDecodeError:
			print("Error parsing line: " + currentString)
			print(traceback.format_exc())
			pass

def getJsonLinesFileJsonStream(f: BinaryIO, max_items: Optional[int] = None) -> Iterator[dict]:
	items_yielded = 0
	for line in f:
		if max_items is not None and items_yielded >= max_items:
			break
		line = line.decode("utf-8", errors="replace")
		try:
			yield json.loads(line)
			items_yielded += 1
		except json.JSONDecodeError:
			print("Error parsing line: " + line)
			traceback.print_exc()
			continue

def getZstBlocksFileJsonStream(f: BinaryIO, max_items: Optional[int] = None) -> Iterator[dict]:
	items_yielded = 0
	for row in ZstBlocksFile.streamRows(f):
		if max_items is not None and items_yielded >= max_items:
			break
		line = row.decode("utf-8", errors="replace")
		try:
			yield json.loads(line)
			items_yielded += 1
		except json.JSONDecodeError:
			print("Error parsing line: " + line)
			traceback.print_exc()
			continue

def getJsonFileStream(f: BinaryIO, max_items: Optional[int] = None) -> Iterator[dict]:
	data = json.loads(f.read())
	items_yielded = 0
	for item in data:
		if max_items is not None and items_yielded >= max_items:
			break
		yield item
		items_yielded += 1

def getFileJsonStream(path: str, f: BinaryIO, max_items: Optional[int] = None) -> Iterator[dict]|None:
	if path.endswith(".jsonl") or path.endswith(".ndjson"):
		return getJsonLinesFileJsonStream(f, max_items)
	elif path.endswith(".zst"):
		return getZstFileJsonStream(f, max_items=max_items)
	elif path.endswith(".zst_blocks"):
		return getZstBlocksFileJsonStream(f, max_items)
	elif path.endswith(".json"):
		return getJsonFileStream(f, max_items)
	else:
		return None