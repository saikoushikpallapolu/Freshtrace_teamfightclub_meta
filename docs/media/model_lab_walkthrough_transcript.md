# Model flow lab - narrated video

Edited walkthrough of actual recorded model outputs. Narration synthesized locally.

Source video: [Pourrissement tomate](https://commons.wikimedia.org/wiki/File:Pourrissement_tomate.webm) by Lionel Allorge, Wikimedia Commons. Selected license: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Changes: resizing, frame sampling, model overlays, edited lab captures and explanatory narration. Derived media uses the same license.

## One sample. One evidence flow.

Welcome to the model flow lab. This edited walkthrough uses captured lab screens and outputs from real Meta API calls. We follow one tomato through an accelerated video, then connect its visual history to an inspection workflow. The product name is still undecided. No live sensor readings were supplied.

## 01 / Voice becomes a request

First, Muse Voice Transcribe turns a spoken request into text. The original tomato video is silent, so this test uses a separately synthesized demonstration request. The real model returned the transcript shown in the lab. That text is included in the history passed to the planner. Here is the demonstration request.

## 02 / Locate and track the tomato

Next, SAM three point one receives the video and the short prompt, tomato. It returns an object box and a pixel mask for the tomato in each analyzed frame. We decoded masks for all one hundred and ten frames and rendered this overlay movie. SAM supplies the object's location and shape. It does not assign an inspection or food safety verdict.

## 03 / Explain the visible changes

Muse Spark analyzes the full video and returns eight structured checkpoint observations. In this run, it described increasing gray textured coverage near the stem, followed by surface depression and wrinkling. The lab lets you select a checkpoint and read the saved observation with its visibility limits. These are visual categories. The accelerated playback does not reveal the real storage duration.

## 04 / Turn evidence into inspection work

Rescue is the decision workflow. Application code maps Spark's visual category to the proposed inspection priority. Here the displayed points increase from thirty five, to seventy, to one hundred as visible concern increases. These are heuristic priority points, not probabilities of spoilage. Because no gas or environmental measurements exist for this video, the sensor channel and combined score remain unavailable.

## 05 / Choose the next useful check

Muse Wonder powers the Investigator planning step. It made a real history tool call, received the saved video observations and returned this read only plan. It compared earlier and later evidence, requested additional views and identified the missing sensor protocol. This is a full clip summary. The model did not perform a physical measurement or an A B group test, and it did not approve stock for sale.

## 06 / Remember and follow up

ShelfWatch keeps the evidence under one batch identity. The timeline connects each checkpoint, mask and observation to the same sample. In the lab you can create a follow up task and mark the demonstration reviewed. Those actions are local to the browser. In the future app, a vendor would confirm an actual inspection or stock outcome, and the next plan would use that saved history.

## Every recommendation has a record

Finally, the model receipts show response identifiers, usage and the planning tool trace. This demonstrates all four required model integrations and how their outputs fit together. The next build step is to connect real batch storage, controlled sensor sessions and human confirmed actions. This video is an explanation of the lab, not evidence of food safety or validated shelf life.
