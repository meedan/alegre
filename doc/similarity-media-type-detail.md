# Similarity Processing by Media Type

This document provides a general outline the steps and calls made by each of the general media types that Meedan's "Alegre" similairty knows how to compute similarity for: Images, Video, Text and Audio.

## Images

![Typical Flow, Check Image Matching](img/alegre-image-flow.png?raw=true "Typical Flow, Check Image Matching")
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

When Searching images, the following events occur:

1. Eventually, during the chain of a sync or async lookup on an existing item, we hit `app.main.lib.image_similarity.search_image`,
2. We pass into `search_image` the hash value of the current item (either as yielded from existing DB record or as received from presto),
3. We then set the value on the image object identified by URL or Doc ID,
4. We then search via PDQ or PHASH, whichever is set,
5. When searching for PDQ we use a custom `bit_count_pdq` function for similarity score in postgres queries,
6. When searching for PHASH we use a custom `bit_count_image` function for similarity score in postgres queries,
7. A set of image records are returned - we then render them in the response to Check API or other requestor.


## Video

![Typical Flow, Check Video Matching](img/alegre-video-flow.png?raw=true "Typical Flow, Check Video Matching")
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

When Searching videos, the following events occur:

1. Eventually, during the chain of a sync or async lookup on an existing item, we hit `app.main.lib.shared_models.video_model.VideoModel.search`,
2. We pass into `search` either the references sufficient to find an existing hash from an existing video, or the data yielded from Presto in order to set that hash value / tmk filepath value,
3. We then identify *all videos that have similar context* and pull up that full list,
4. We then calculate `l1` scores based off the simplistic hash stored on the objects to determine candidates for deeper analysis,
5. We then conduct a more thorough TMK-based analysis for videos passing the candidate test,
6. We return the list of matching TMK-based results.

## Text

![Typical Flow, Check Text Matching](img/alegre-text-flow.png?raw=true "Typical Flow, Check Text Matching")
[Edit Link](https://docs.google.com/drawings/d/12WljT8-qsUi8xG584clD_eV1ABOcB6CqkMX0eAxSPrE/edit)

For text, Check-API receives new `ProjectMedia` items and, as they are created, performs the following procedures:

1. Store the `ProjectMedia`,
2. Send the `ProjectMedia` through `Bot::Alegre.run`,
3. `Bot::Alegre.run` searches for items via video fingerprinting,
4. Matches are simultaneously checked asynchronously for suggested and confirmed items *for `original_title` and `original_description`*, *for all vector models applied*,
5. Once both queries are completed *for both fields*, *for all vector models applied*, we process the item in a callback, and store results in `Bot::Alegre.relate_project_media_callback` - that method tracks remaining messages and only processes a match when all messages are no longer in flight,
6. Relationships at the Check API level are persisted after (5).

When Searching text, the following events occur:

1. Eventually, during the chain of a sync or async lookup on an existing item, we hit `app.main.lib.text_similarity.search_text` (after waiting to pass on to this step until all vectors are completed, subject to `elastic_crud.requires_encoding`),
2. We pass into `search_text` the OpenSearch document which contains all completed relevant vectors along with the list of models from which we will process search results,
3. For each model, including elasticsearch, we search for results from OpenSearch - using language analyzers where applicable with opensearch, else, cosine similarity searches with vectors.
4. We append results into a large list of results, each item of which contains sufficient data to indicate the model that yielded the result.

## Audio

![Typical Flow, Check Audio Matching](img/alegre-audio-flow.png?raw=true "Typical Flow, Check Audio Matching")
[Edit Link](https://docs.google.com/drawings/d/1YwWJMgPxAlonCdq4M5RWaSOzSSucwHkg7EWTggWOhw8/edit)

For audio, Check-API receives new `ProjectMedia` items and, as they are created, performs the following procedures:

1. Store the `ProjectMedia`,
2. Send the `ProjectMedia` through `Bot::Alegre.run`,
3. `Bot::Alegre.run` searches for items via video fingerprinting,
4. Matches are simultaneously checked asynchronously for suggested and confirmed items,
5. Once both queries are completed, we process the item in a callback, and store results in `Bot::Alegre.relate_project_media_callback`,
6. We also store transcription text annotations in the text index for the item, which will match subsequent items (but does *not* match against existing items for the transcription attempt),
7. Transcription data is exhausted into OpenSearch for text lookups, and Audio Hashes are exhausted into Postgres for audio lookups on Alegre
8. Relationships at the Check API level are persisted after (5).

When Searching text, the following events occur:

1. Eventually, during the chain of a sync or async lookup on an existing item, we hit `app.main.lib.shared_models.audio_model.AudioModel.search`,
2. We pass into `search` either the references sufficient to find an existing hash from an existing audio, or the data yielded from Presto in order to set that chromaprint hash value,
3. We then run that hash through the custom postgres/perl script `get_audio_chromaprint_score` in order to calculate similarity,
4. We then return all matches yielded.

