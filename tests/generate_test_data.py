#!/usr/bin/env python3
"""
Generate mock test data for Phase 4 pipeline testing.
Creates a small Parquet file with simulated business idea posts.
"""

import os
import polars as pl
import random
from datetime import datetime, timedelta

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "data")

# Sample business ideas grouped by theme (for clustering)
IDEA_CLUSTERS = {
    "productivity_tools": [
        "I wish there was an app that could block distracting websites during work hours automatically",
        "Someone should build a tool that tracks how much time I spend in meetings vs actual work",
        "There needs to be a better way to manage my daily tasks without a complex UI",
        "I would pay for an app that forces me to take breaks every hour - my eyes are killing me",
        "Why isn't there a simple desktop app that shows my calendar appointments as a sidebar all day?",
        "A tool that automatically schedules my deep work blocks based on my meeting-free times would be amazing",
        "I need something that keeps track of what I'm working on and generates weekly reports for my manager",
        "Someone please build a focus timer that integrates with Slack to set my status automatically",
    ],
    "developer_tools": [
        "There should be a VS Code extension that explains code changes in plain English",
        "I want a CLI tool that automatically generates READMEs from code comments",
        "Why is there no simple tool to sync my dotfiles across multiple machines?",
        "An AI that reviews my code and suggests improvements before I push would save so much time",
        "Someone needs to build a better diff viewer for large JSON files",
        "I wish there was a tool that automatically keeps my node_modules up to date and tests for breaking changes",
        "A browser extension that lets me save API documentation snippets and search them later",
        "There should be an easy way to generate test data for any API endpoint",
    ],
    "health_fitness": [
        "I want an app that reminds me to drink water but actually works with my schedule",
        "Why isn't there a meal planning app that considers what's already in my fridge?",
        "Someone should make a fitness app for people who hate the gym - just home workouts",
        "An app that tracks my sleep and suggests when I should go to bed based on my schedule",
        "I need something that counts my steps without draining my phone battery",
        "There should be a nutrition app that scans barcodes and tells me if it fits my diet goals",
        "A stretching reminder app for desk workers that actually shows proper form",
        "Why isn't there an app that matches me with workout partners at my skill level?",
    ],
    "personal_finance": [
        "I wish there was a simple app that rounds up my purchases and invests the change",
        "Someone should build a service that negotiates my bills for me automatically",
        "There needs to be a better way to split rent and utilities with roommates",
        "An app that predicts my upcoming expenses based on my purchase history would help so much",
        "I want something that tracks subscriptions and alerts me before renewal dates",
        "A tool that analyzes my spending and suggests where I'm overpaying compared to averages",
        "Why isn't there an app that helps me save for specific goals by rounding up purchases?",
        "Someone should make a price tracker that notifies me when things I want go on sale",
    ],
    "small_business": [
        "There should be a simple invoicing tool for freelancers that doesn't cost $30/month",
        "I need an easy way to schedule social media posts without learning a complex platform",
        "An AI that responds to basic customer service emails would save my small business hours daily",
        "Someone should build a CRM specifically designed for solo consultants",
        "I wish there was a tool that generates SEO-optimized product descriptions from photos",
        "A booking system for small service businesses that's actually affordable and simple",
        "Why isn't there an inventory management app that works offline for pop-up shops?",
        "There needs to be a better way to collect and display customer testimonials",
    ],
    "noise_ideas": [  # These won't cluster well
        "Random post about cats that doesn't relate to anything business",
        "Just here to say this subreddit is awesome",
        "Has anyone seen the new movie? It's great",
        "Looking for recommendations for a good restaurant downtown",
        "My dog learned a new trick today",
    ],
}


def generate_test_data(num_rows: int = 50) -> pl.DataFrame:
    """Generate a test DataFrame with clustered business ideas."""
    
    data = {
        "id": [],
        "body": [],
        "subreddit": [],
        "author": [],
        "score": [],
        "created_utc": [],
        "quality_score": [],
    }
    
    base_time = datetime(2024, 1, 1)
    subreddits = ["startups", "Entrepreneur", "SideProject", "smallbusiness", "business"]
    
    # Generate data by sampling from clusters
    clusters = list(IDEA_CLUSTERS.keys())
    
    for i in range(num_rows):
        cluster = random.choice(clusters)
        ideas = IDEA_CLUSTERS[cluster]
        
        data["id"].append(f"test_{i:04d}")
        data["body"].append(random.choice(ideas))
        data["subreddit"].append(random.choice(subreddits))
        data["author"].append(f"user_{random.randint(1000, 9999)}")
        data["score"].append(random.randint(1, 500))
        data["created_utc"].append(int((base_time + timedelta(days=random.randint(0, 365))).timestamp()))
        data["quality_score"].append(round(random.uniform(0.3, 0.95), 2))
    
    return pl.DataFrame(data)


def main():
    """Create test data directory and generate test Parquet file."""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    df = generate_test_data(num_rows=50)
    output_path = os.path.join(TEST_DATA_DIR, "test_chains.parquet")
    
    df.write_parquet(output_path)
    print(f"Generated test data: {output_path}")
    print(f"Rows: {df.height}, Columns: {df.columns}")
    
    # Also save a sample CSV for inspection
    csv_path = os.path.join(TEST_DATA_DIR, "test_chains.csv")
    df.write_csv(csv_path)
    print(f"Also saved CSV: {csv_path}")


if __name__ == "__main__":
    main()
