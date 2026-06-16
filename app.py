import os
from flask import Flask, jsonify, request, render_template
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__, template_folder='templates', static_folder='static')

# Catalog of items (Movies & Books)
ITEMS = [
    # Movies
    {
        "id": "m1",
        "title": "Interstellar",
        "author_director": "Christopher Nolan",
        "type": "Movie",
        "genres": ["Sci-Fi", "Drama", "Adventure"],
        "description": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival. Beautiful space travel, time dilation, and deep emotional father-daughter connection.",
        "year": 2014,
        "rating_avg": 4.7
    },
    {
        "id": "m2",
        "title": "Inception",
        "author_director": "Christopher Nolan",
        "type": "Movie",
        "genres": ["Sci-Fi", "Action", "Thriller"],
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O. Complex layers of reality and heist thrill.",
        "year": 2010,
        "rating_avg": 4.8
    },
    {
        "id": "m3",
        "title": "The Godfather",
        "author_director": "Francis Ford Coppola",
        "type": "Movie",
        "genres": ["Drama", "Crime"],
        "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son. Masterpiece of mafia family struggles, honor, and betrayal.",
        "year": 1972,
        "rating_avg": 4.9
    },
    {
        "id": "m4",
        "title": "The Dark Knight",
        "author_director": "Christopher Nolan",
        "type": "Movie",
        "genres": ["Action", "Crime", "Thriller"],
        "description": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
        "year": 2008,
        "rating_avg": 4.9
    },
    {
        "id": "m5",
        "title": "La La Land",
        "author_director": "Damien Chazelle",
        "type": "Movie",
        "genres": ["Romance", "Musical", "Drama"],
        "description": "While navigating their careers in Los Angeles, a pianist and an actress fall in love while attempting to reconcile their aspirations for the future. Colorful, emotional, and jazz-centric romantic musical.",
        "year": 2016,
        "rating_avg": 4.5
    },
    {
        "id": "m6",
        "title": "Before Sunrise",
        "author_director": "Richard Linklater",
        "type": "Movie",
        "genres": ["Romance", "Drama"],
        "description": "A young man and woman meet on a train in Europe, and wind up spending one evening together in Vienna. A beautiful talkative romance exploring life, love, and connection.",
        "year": 1995,
        "rating_avg": 4.6
    },
    {
        "id": "m7",
        "title": "Parasite",
        "author_director": "Bong Joon Ho",
        "type": "Movie",
        "genres": ["Thriller", "Drama", "Comedy"],
        "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan. Dark humor, shocking twists, and social commentary.",
        "year": 2019,
        "rating_avg": 4.7
    },
    {
        "id": "m8",
        "title": "Spirited Away",
        "author_director": "Hayao Miyazaki",
        "type": "Movie",
        "genres": ["Fantasy", "Animation", "Family"],
        "description": "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits, and where humans are changed into beasts. Ghibli masterpiece.",
        "year": 2001,
        "rating_avg": 4.8
    },
    # Books
    {
        "id": "b1",
        "title": "Dune",
        "author_director": "Frank Herbert",
        "type": "Book",
        "genres": ["Sci-Fi", "Fantasy", "Adventure"],
        "description": "Set in the far future amidst a sprawling feudal interstellar empire, Dune tells the story of Paul Atreides as his family accepts control of the desert planet Arrakis, source of the spice.",
        "year": 1965,
        "rating_avg": 4.7
    },
    {
        "id": "b2",
        "title": "Neuromancer",
        "author_director": "William Gibson",
        "type": "Book",
        "genres": ["Sci-Fi", "Cyberpunk", "Thriller"],
        "description": "A matrix hacker is hired for one last job by a mysterious employer, sending him into an expansive virtual reality hacking adventure. The definitive classic that defined the cyberpunk genre.",
        "year": 1984,
        "rating_avg": 4.4
    },
    {
        "id": "b3",
        "title": "The Great Gatsby",
        "author_director": "F. Scott Fitzgerald",
        "type": "Book",
        "genres": ["Drama", "Classics", "Romance"],
        "description": "The story of the mysteriously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan. A critique of the American Dream in the Roaring Twenties, full of tragedy and class tension.",
        "year": 1925,
        "rating_avg": 4.3
    },
    {
        "id": "b4",
        "title": "Pride and Prejudice",
        "author_director": "Jane Austen",
        "type": "Book",
        "genres": ["Romance", "Classics", "Drama"],
        "description": "Sparks fly when spirited Elizabeth Bennet meets single, rich, and proud Mr. Darcy. But Mr. Darcy reluctantly finds himself falling in love with a woman beneath his class. Romantic classic.",
        "year": 1813,
        "rating_avg": 4.6
    },
    {
        "id": "b5",
        "title": "The Hobbit",
        "author_director": "J.R.R. Tolkien",
        "type": "Book",
        "genres": ["Fantasy", "Adventure", "Classics"],
        "description": "Bilbo Baggins, a hobbit enjoying a quiet life, is swept into a quest by the wizard Gandalf and thirteen dwarves to reclaim their home and gold from the dragon Smaug. Whimsical adventure.",
        "year": 1937,
        "rating_avg": 4.8
    },
    {
        "id": "b6",
        "title": "The Silent Patient",
        "author_director": "Alex Michaelides",
        "type": "Book",
        "genres": ["Thriller", "Mystery", "Psychological"],
        "description": "Alicia Berenson's life is seemingly perfect. One evening she shoots her husband five times in the face, and then never speaks another word. A criminal psychotherapist tries to solve her mystery.",
        "year": 2019,
        "rating_avg": 4.5
    },
    {
        "id": "b7",
        "title": "Atomic Habits",
        "author_director": "James Clear",
        "type": "Book",
        "genres": ["Self-Help", "Non-Fiction", "Productivity"],
        "description": "No matter your goals, Atomic Habits offers a proven framework for improving every day. Learn how tiny habits compound into massive, life-changing self-improvement results.",
        "year": 2018,
        "rating_avg": 4.8
    },
    {
        "id": "b8",
        "title": "Sapiens",
        "author_director": "Yuval Noah Harari",
        "type": "Book",
        "genres": ["History", "Non-Fiction", "Anthropology"],
        "description": "Spanning the entirety of human history, Sapiens explores how cognitive, agricultural, and scientific revolutions shaped our species and the modern world we live in.",
        "year": 2011,
        "rating_avg": 4.7
    }
]

# Database of mock users and their ratings
MOCK_USERS = {
    "Alex (Sci-Fi Enthusiast)": {
        "m1": 5, "m2": 5, "b1": 5, "b2": 4, "b4": 1, "m5": 2
    },
    "Sophia (Romance Romantic)": {
        "m5": 5, "m6": 5, "b4": 5, "b3": 4, "m2": 2, "m4": 1
    },
    "Marcus (Thriller / Crime Fan)": {
        "b6": 5, "m4": 5, "m2": 4, "m7": 5, "m5": 1, "m3": 4
    },
    "Emma (Fantasy & Adventure Lover)": {
        "b5": 5, "m8": 5, "b1": 4, "m1": 4, "b4": 2, "m6": 2
    },
    "Liam (Non-Fiction & Drama Reader)": {
        "b8": 5, "b7": 5, "b3": 4, "m3": 4, "m2": 3, "m6": 3
    }
}

# Add initial custom item store in memory
CUSTOM_ITEMS = []

def get_all_items():
    return ITEMS + CUSTOM_ITEMS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/items', methods=['GET'])
def api_items():
    return jsonify(get_all_items())

@app.route('/api/mock_users', methods=['GET'])
def api_mock_users():
    return jsonify(list(MOCK_USERS.keys()))

@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    data = request.get_json() or {}
    ratings = data.get('ratings', {})
    algorithm = data.get('algorithm', 'content') # 'content' or 'collaborative'
    
    # Filter keys to match strings
    ratings = {str(k): float(v) for k, v in ratings.items()}
    
    all_items = get_all_items()
    item_dict = {item['id']: item for item in all_items}
    
    if not ratings:
        # If no ratings, return popular items as fallback
        popular_recommendations = sorted(all_items, key=lambda x: x['rating_avg'], reverse=True)[:5]
        return jsonify({
            "recommendations": [
                {"item": item, "score": item['rating_avg'], "reason": "Popular Choice"} 
                for item in popular_recommendations
            ],
            "algorithm": algorithm,
            "details": {
                "summary": "You haven't rated any items yet! Showing top popular items in our catalog.",
                "math_steps": ["No user ratings provided.", "Defaulted to sorting items by their global average rating."]
            }
        })
        
    if algorithm == 'content':
        results, details = compute_content_based(ratings, all_items)
    else:
        results, details = compute_collaborative(ratings, all_items)
        
    return jsonify({
        "recommendations": results,
        "algorithm": algorithm,
        "details": details
    })

@app.route('/api/add_item', methods=['POST'])
def api_add_item():
    data = request.get_json() or {}
    title = data.get('title')
    author_director = data.get('author_director')
    item_type = data.get('type', 'Movie')
    genres_raw = data.get('genres', '')
    description = data.get('description', '')
    year_raw = data.get('year')
    
    if not title or not author_director or not genres_raw or not description:
        return jsonify({"error": "Missing required fields"}), 400
        
    genres = [g.strip() for g in genres_raw.split(',') if g.strip()]
    try:
        year = int(year_raw)
    except:
        year = 2026
        
    new_id = f"custom_{len(CUSTOM_ITEMS) + 1}"
    new_item = {
        "id": new_id,
        "title": title,
        "author_director": author_director,
        "type": item_type,
        "genres": genres,
        "description": description,
        "year": year,
        "rating_avg": 4.0
    }
    
    CUSTOM_ITEMS.append(new_item)
    return jsonify({"success": True, "item": new_item})


def compute_content_based(user_ratings, all_items):
    # Prepare corpus for TF-IDF vectorizer
    # Combine genres and descriptions into a single metadata document
    corpus = []
    item_ids = []
    
    for item in all_items:
        text = " ".join(item['genres']) * 3 + " " + item['description'] + " " + item['author_director']
        corpus.append(text)
        item_ids.append(item['id'])
        
    # Fit TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus).toarray()
    
    # Map item ID to its vector index
    id_to_idx = {item_id: idx for idx, item_id in enumerate(item_ids)}
    
    # Calculate user preference vector
    # Center the ratings around the mid-point 3.0 (i.e. ratings > 3 positive, ratings < 3 negative)
    user_vector = np.zeros(tfidf_matrix.shape[1])
    rated_count = 0
    
    details_math = []
    weighted_terms = []
    
    for item_id, rating in user_ratings.items():
        if item_id in id_to_idx:
            idx = id_to_idx[item_id]
            weight = rating - 2.5 # Weight is positive for stars > 2.5, negative for <= 2.5
            user_vector += weight * tfidf_matrix[idx]
            rated_count += 1
            details_math.append(f"Rated '{all_items[idx]['title']}' as {rating} stars (Weight: {weight:+.1f})")
            
    if rated_count == 0 or np.linalg.norm(user_vector) == 0:
        # Fallback if no weights
        user_vector = np.mean(tfidf_matrix, axis=0)
        details_math.append("No rated items were found in catalog index. Defaulted to average catalog vector.")
    
    # Get top TF-IDF words for user profile vector to explain recommendations
    feature_names = vectorizer.get_feature_names_out()
    top_indices = np.argsort(user_vector)[::-1][:6]
    top_words = [(feature_names[idx], float(user_vector[idx])) for idx in top_indices if user_vector[idx] > 0]
    
    # Compute Cosine Similarity between user vector and all items
    user_vector_norm = user_vector.reshape(1, -1)
    similarities = cosine_similarity(user_vector_norm, tfidf_matrix)[0]
    
    recommendations = []
    for idx, item in enumerate(all_items):
        item_id = item['id']
        # Do not recommend items the user already rated
        if item_id in user_ratings:
            continue
            
        score = float(similarities[idx])
        # Format a reason
        # Find which genre matches best
        matched_genres = [g for g in item['genres'] if any(word.lower() in g.lower() for word, w in top_words)]
        if matched_genres:
            reason = f"Matches your interest in {', '.join(matched_genres)}"
        else:
            reason = f"Highly matches your content taste profile"
            
        recommendations.append({
            "item": item,
            "score": round(score, 3),
            "reason": reason
        })
        
    # Sort by score descending
    recommendations = sorted(recommendations, key=lambda x: x['score'], reverse=True)[:5]
    
    # Generate summary details
    top_word_strings = [f"'{word}' ({weight:.2f})" for word, weight in top_words]
    details = {
        "summary": f"Based on your profile, your top interest signals are: {', '.join(top_word_strings[:4]) if top_word_strings else 'General'}.",
        "math_steps": [
            "Step 1: Extracted TF-IDF keyword matrices for all movies and books.",
            f"Step 2: Compiled your User Preference Vector by summing rated item vectors weighted by their distance from 2.5 stars:",
            *details_math,
            f"Step 3: Identified your peak keyword interests: {', '.join(top_word_strings[:5])}",
            "Step 4: Ran Cosine Similarity comparison between your Preference Vector and all unrated catalog items.",
            "Step 5: Selected the top 5 highest-similarity items."
        ],
        "top_keywords": [{"word": word, "weight": round(weight, 3)} for word, weight in top_words]
    }
    
    return recommendations, details


def compute_collaborative(user_ratings, all_items):
    # Collaborative Filtering: User-Based
    # 1. Build rating matrix: active user + mock users
    # Get all item IDs
    all_item_ids = [item['id'] for item in all_items]
    item_id_to_title = {item['id']: item['title'] for item in all_items}
    
    # Prepare a list of dictionaries for pandas DataFrame
    matrix_data = []
    
    # Add mock users
    for user_name, ratings in MOCK_USERS.items():
        row = {"user_name": user_name}
        for item_id in all_item_ids:
            row[item_id] = ratings.get(item_id, np.nan)
        matrix_data.append(row)
        
    # Add active user
    active_row = {"user_name": "Active User"}
    for item_id in all_item_ids:
        active_row[item_id] = user_ratings.get(item_id, np.nan)
    matrix_data.append(active_row)
    
    df = pd.DataFrame(matrix_data).set_index("user_name")
    
    # Calculate similarities using Pearson Correlation
    # Pearson handles user rating bias (some users rate everything high, some low) by subtracting mean
    active_user_series = df.loc["Active User"]
    active_mean = active_user_series.mean()
    active_centered = active_user_series - active_mean
    
    similarities = {}
    math_details = []
    math_details.append(f"Active User Rating Mean: {active_mean:.2f}")
    
    for other_user in MOCK_USERS.keys():
        other_series = df.loc[other_user]
        other_mean = other_series.mean()
        other_centered = other_series - other_mean
        
        # Find shared items
        shared_mask = active_user_series.notna() & other_series.notna()
        shared_count = shared_mask.sum()
        
        if shared_count < 2:
            # Not enough shared ratings to compute correlation; default to cosine-like similarity over shared or 0
            similarities[other_user] = 0.0
            math_details.append(f"Comparison with '{other_user}': Insufficient shared ratings (need >= 2, shared {shared_count}). Similarity set to 0.0.")
            continue
            
        # Pearson correlation equation
        u_vals = active_centered[shared_mask]
        v_vals = other_centered[shared_mask]
        
        num = np.sum(u_vals * v_vals)
        den = np.sqrt(np.sum(u_vals**2)) * np.sqrt(np.sum(v_vals**2))
        
        if den == 0:
            sim = 0.0
        else:
            sim = float(num / den)
            
        similarities[other_user] = sim
        math_details.append(f"Pearson Correlation with '{other_user}': {sim:+.3f} (shared {shared_count} ratings)")
        
    # Now predict ratings for unrated items
    predictions = []
    
    # We only consider neighbors with similarity > 0 to make predictions
    positive_neighbors = {u: sim for u, sim in similarities.items() if sim > 0}
    
    if not positive_neighbors:
        # Fallback if no similar users found
        popular_fallback = sorted(all_items, key=lambda x: x['rating_avg'], reverse=True)
        fallback_recommendations = []
        for item in popular_fallback:
            if item['id'] not in user_ratings:
                fallback_recommendations.append({
                    "item": item,
                    "score": item['rating_avg'],
                    "reason": "Popular choice (No similar users found)"
                })
        math_details.append("No positive correlation neighbors found. Recommending popular items instead.")
        return fallback_recommendations[:5], {
            "summary": "No other users match your rating patterns yet. Showing popular titles in the meantime.",
            "math_steps": math_details,
            "similarities": [{"user": user, "score": 0.0} for user in MOCK_USERS.keys()]
        }
        
    # Predict unrated items
    for item in all_items:
        item_id = item['id']
        if item_id in user_ratings:
            continue
            
        weighted_sum = 0.0
        sim_sum = 0.0
        contributing_users = []
        
        for neighbor, sim in positive_neighbors.items():
            neighbor_rating = MOCK_USERS[neighbor].get(item_id)
            if neighbor_rating is not None:
                # Get neighbor's mean rating to adjust for bias
                neighbor_mean = df.loc[neighbor].mean()
                # Weighted difference from neighbor mean
                weighted_sum += sim * (neighbor_rating - neighbor_mean)
                sim_sum += abs(sim)
                contributing_users.append(f"{neighbor} (liked it {neighbor_rating}★, similarity {sim:.2f})")
                
        if sim_sum > 0:
            predicted_rating = active_mean + (weighted_sum / sim_sum)
            # Clip between 1.0 and 5.0
            predicted_rating = float(np.clip(predicted_rating, 1.0, 5.0))
            
            # Formulate description of contributors
            if contributing_users:
                reason = f"Liked by similar user: {contributing_users[0].split(' (')[0]}"
            else:
                reason = "Highly matching your peer group taste"
                
            predictions.append({
                "item": item,
                "score": round(predicted_rating, 2),
                "reason": reason,
                "contributors": contributing_users[:3]
            })
            
    # Sort predictions by score descending
    predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)[:5]
    
    # Sort similarities for output representation
    sorted_sims = [{"user": u, "score": round(s, 3)} for u, s in sorted(similarities.items(), key=lambda x: x[1], reverse=True)]
    
    details = {
        "summary": f"Your ratings are most similar to: {sorted_sims[0]['user']} (Score: {sorted_sims[0]['score']:+.2f}).",
        "math_steps": [
            "Step 1: Extracted a user-item rating grid including you and 5 mock user personas.",
            "Step 2: Computed Pearson Correlation similarity matrix between your ratings and other users:",
            *math_details,
            "Step 3: Identified neighbors with positive correlation coefficients.",
            "Step 4: Predicted your ratings for unrated items using similarity-weighted ratings adjusted for user biases.",
            "Step 5: Picked the top 5 highest-predicted items."
        ],
        "similarities": sorted_sims
    }
    
    return predictions, details

if __name__ == '__main__':
    # Flask runner
    app.run(debug=True, port=5000)
