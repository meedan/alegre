# How Check Processes Items For Similarity

## Images

![Typical Flow, Check Image Matching](doc/img/alegre-image-flow.png?raw=true "Typical Flow, Check Image Matching")
[Edit Link](https://docs.google.com/drawings/d/1jXgbM_06rlpPeip1vxUKpiRYyhumrkFlr-2EC3qBxHg/edit)

At a high level, Check-API receives new `ProjectMedia` items and, as they are created, we perform the following procedures:

1. Store the `ProjectMedia`,
2. Send the `ProjectMedia` through `Bot::Alegre.run`,
3. `Bot::Alegre.run` searches for items via image hashing,
4. Matches are simultaneously checked asynchronously for suggested and confirmed items,
5. Once both queries are completed, we process the item in a callback, and store results in `Bot::Alegre.relate_project_media_callback`,
6. We also store OCR text annotations in the text index for the item, which will match subsequent items (but does *not* match against existing items for the OCR attempt),
7. OCR data is exhausted into OpenSearch for text lookups, and Image Hashes are exhausted into Postgres for image lookups on Alegre,
8. Relationships at the Check API level are persisted after (5).

## Video

![Typical Flow, Check Video Matching](doc/img/alegre-video-flow.png?raw=true "Typical Flow, Check Video Matching")
[Edit Link](https://docs.google.com/drawings/d/1HQTwHmkhzp-J742-QAowfYMNaYoALYTPwOTA-PASHnk/edit)

For video, Check-API receives new `ProjectMedia` items and, as they are created, performs the following procedures:

1. Store the `ProjectMedia`,
2. Send the `ProjectMedia` through `Bot::Alegre.run`,
3. `Bot::Alegre.run` searches for items via video fingerprinting,
4. Matches are simultaneously checked asynchronously for suggested and confirmed items,
5. Once both queries are completed, we process the item in a callback, and store results in `Bot::Alegre.relate_project_media_callback`,
6. We also store transcription text annotations in the text index for the item, which will match subsequent items (but does *not* match against existing items for the transcription attempt),
7. Transcription data is exhausted into OpenSearch for text lookups, and Video Hashes are exhausted into Postgres for video lookups on Alegre, as well as on a disk lookup for .tmk file lookups,
8. Relationships at the Check API level are persisted after (5).

## Text

![Typical Flow, Check Text Matching](doc/img/alegre-text-flow.png?raw=true "Typical Flow, Check Text Matching")
[Edit Link](https://docs.google.com/drawings/d/12WljT8-qsUi8xG584clD_eV1ABOcB6CqkMX0eAxSPrE/edit)

1. Store the `ProjectMedia`,
2. Send the `ProjectMedia` through `Bot::Alegre.run`,
3. `Bot::Alegre.run` searches for items via video fingerprinting,
4. Matches are simultaneously checked asynchronously for suggested and confirmed items *for `original_title` and `original_description`*, *for all vector models applied*,
5. Once both queries are completed *for both fields*, *for all vector models applied*, we process the item in a callback, and store results in `Bot::Alegre.relate_project_media_callback` - that method tracks remaining messages and only processes a match when all messages are no longer in flight,
6. Relationships at the Check API level are persisted after (5).

## Audio

![Typical Flow, Check Audio Matching](doc/img/alegre-audio-flow.png?raw=true "Typical Flow, Check Audio Matching")
[Edit Link](https://docs.google.com/drawings/d/1YwWJMgPxAlonCdq4M5RWaSOzSSucwHkg7EWTggWOhw8/edit)

1. Store the `ProjectMedia`,
2. Send the `ProjectMedia` through `Bot::Alegre.run`,
3. `Bot::Alegre.run` searches for items via video fingerprinting,
4. Matches are simultaneously checked asynchronously for suggested and confirmed items,
5. Once both queries are completed, we process the item in a callback, and store results in `Bot::Alegre.relate_project_media_callback`,
6. We also store transcription text annotations in the text index for the item, which will match subsequent items (but does *not* match against existing items for the transcription attempt),
7. Transcription data is exhausted into OpenSearch for text lookups, and Audio Hashes are exhausted into Postgres for audio lookups on Alegre
8. Relationships at the Check API level are persisted after (5).
