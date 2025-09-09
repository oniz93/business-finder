**Objective:**
You are an expert AI/ML engineer. Your task is to provide a detailed, step-by-step development plan to analyze a 3TB compressed text dataset of Reddit posts and comments to identify, aggregate, and develop business ideas. I will execute this plan on a dedicated server with the following specifications: 20 CPU cores, 40GB RAM, and 8x NVIDIA A4000 GPUs (16GB VRAM each).

The plan must incorporate a **dedicated vector database (Qdrant)** for embeddings and a **hybrid search system (Elasticsearch + Semantic Search)** for the final output. The final business plan generation must be heavily parallelized using **Google's Gemini 1.5 Pro model with an asynchronous API**.

The plan is broken down into four distinct phases:
1.  **Phase 1: Environment Setup and High-Efficiency Data Ingestion.**
2.  **Phase 2: High-Speed Filtering for "Pain Points" and "Ideas".**
3.  **Phase 3: AI-Powered Aggregation using a Vector Database.**
4.  **Phase 4: Massively Parallel Business Plan Generation & Hybrid Storage.**

---

#### **Phase 1: Environment Setup & High-Efficiency Data Ingestion**

*   **Goal:** Set up the server environment and establish a reliable, memory-efficient pipeline to read and process the 3TB dataset in a stream directly from the compressed Zstandard (`.zst`) files.
*   **Key Libraries:** `zstandard`, `json`, `dask`, `pandas`, `docker`.
*   **Plan:**
    1.  **Environment:** Create a Python environment. Install key libraries: `dask`, `pandas`, `zstandard`, `jupyterlab`, `elasticsearch-dsl`, `qdrant-client`, and the new `google-generativeai`. Also, install GPU-related libraries: `pytorch`, `transformers`, `sentence-transformers`, and `cuml`.
    2.  **Database Setup:** Use Docker and `docker-compose` to launch containers for **Qdrant** and **Elasticsearch**.
    3.  **Data Ingestion Strategy:** Stream-process the data using a Python generator function that reads `.zst` files line-by-line, avoiding full decompression to disk.
    4.  **Action:** Use **Dask Bag** to parallelize the processing of the stream from the generator across all 20 CPU cores.

---

#### **Phase 2: High-Speed Filtering for "Pain Points" and "Ideas"**

*   **Goal:** Rapidly scan the data stream to filter it down to a much smaller, high-value subset of comments/posts that likely contain business ideas or user frustrations.
*   **Key Libraries:** `dask`, `transformers`.
*   **Plan:**
    1.  **Multi-Stage Filtering:** Apply a fast, rule-based heuristic filter for trigger phrases, followed by a more accurate, lightweight NLP classification model (e.g., DistilBERT) to classify items into `idea` or `pain_point`.
    2.  **Action:** Chain these filters on the Dask Bag stream and materialize the final, high-value dataset into a set of **Parquet files**. This dataset is now clean and ready for deep analysis.

---

#### **Phase 3: AI-Powered Aggregation using a Vector Database**

*   **Goal:** Convert the filtered ideas into vector embeddings, store them in Qdrant, and then cluster them to find overarching business opportunities.
*   **Key Libraries:** `sentence-transformers`, `qdrant-client`, RAPIDS `cuml`.
*   **Plan:**
    1.  **Embedding:** Use a `sentence-transformers` model to convert the text of each idea from the Parquet files into a vector embedding, parallelizing this across all 8 GPUs.
    2.  **Vector Storage:** As embeddings are generated, push them into a **Qdrant collection**. Store the source post ID and text in the vector's payload.
    3.  **Clustering:** Retrieve all embeddings from Qdrant and use the GPU-accelerated **HDBSCAN** algorithm from `cuml` to identify clusters of similar ideas.
    4.  **LLM Synthesis:** For each cluster, sample representative texts and use an LLM (this can be Gemini as well) to generate a concise 1-2 sentence summary of the core business opportunity.
    5.  **Action:** Store the final summarized opportunities in a single structured file, `summaries.csv`, ready for the final generation phase.

---

#### **Phase 4: Massively Parallel Business Plan Generation & Hybrid Storage**

*   **Goal:** Use Google's Gemini 2.5 Pro to generate a full business plan for *every* summarized opportunity in a highly parallel, asynchronous fashion. Store the results in a hybrid system (Elasticsearch and Qdrant) for advanced searching.
*   **Key Libraries:** `google-generativeai`, `asyncio`, `elasticsearch-dsl`, `qdrant-client`.
*   **Plan:**
    1.  **Setup for Asynchronous Generation:**
        *   Obtain a Google AI API Key and configure it in your environment.
        *   The `google-generativeai` library provides an asynchronous client out of the box, which we will use.
    2.  **Define an Asynchronous Generation Function:**
        *   Create a Python `async` function (e.g., `async def generate_business_plan(opportunity_summary)`).
        *   Inside this function, instantiate the Gemini model (`GenerativeModel("gemini-1.5-pro-latest")`).
        *   Format the detailed business plan prompt using the opportunity summary.
        *   Call the model using `await model.generate_content_async(prompt)`. This non-blocking call allows the program to work on other requests while waiting for the API response.
        *   Return the complete, structured business plan.
    3.  **Parallel Execution with `asyncio`:**
        *   Write a main `async` function that reads all opportunity summaries from `summaries.csv`.
        *   Create a list of concurrent tasks by calling `generate_business_plan()` for *each* summary.
        *   Use **`asyncio.gather(*tasks)`** to execute all these API calls concurrently. This is the key to heavy parallelization, allowing you to send hundreds or thousands of requests to the Gemini API at once, dramatically reducing the total generation time from hours/days to minutes.
    4.  **Hybrid Storage (Asynchronously):**
        *   Once `asyncio.gather` completes, you will have a list of all the generated business plans.
        *   Process this list and store each plan in your dual-database system:
            *   **Elasticsearch:** Store the full JSON of the business plan for keyword search. The `async-elasticsearch` library can be used to do this without blocking.
            *   **Qdrant:** Generate a new embedding from each plan's executive summary and store this vector in a new `business_plans` collection. The Qdrant client also supports async operations.
*   **Action:**
    1.  Write the `async def generate_business_plan()` function.
    2.  Write the main `async def main()` function to read the CSV and use `asyncio.gather` to collect all the generated plans.
    3.  Run the main script with `asyncio.run(main())`.
    4.  Write an asynchronous function to iterate through the collected results and perform the dual-storage operation, pushing data to Elasticsearch and Qdrant in parallel.
