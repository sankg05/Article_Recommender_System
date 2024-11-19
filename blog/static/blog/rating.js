document.addEventListener("DOMContentLoaded", function () {
    const interactiveStars = document.querySelectorAll(".rating-interactive .fa-star");

    // Highlight stars on mouseover
    interactiveStars.forEach(star => {
        star.addEventListener("mouseover", function () {
            const value = this.getAttribute("data-value");
            highlightStars(value);
        });

        star.addEventListener("mouseout", function () {
            const userRating = document.querySelector(".rating-interactive").getAttribute("data-user-rating");
            highlightStars(userRating);  // Revert to the user's rating on mouse out
        });

        // Handle click to submit the rating
        star.addEventListener("click", function () {
            const value = this.getAttribute("data-value");
            const postId = this.getAttribute("data-post-id");

            if (value && postId) {
                fetch(`/rate/${postId}/${value}/`, {
                    method: 'GET',
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log("Rating submitted:", data.message);

                        // Update the user rating display (stars)
                        updateUserRatingDisplay(data.user_rating);
                        updateAverageRatingDisplay(data.average_rating);
                    } else {
                        console.error("Error submitting rating:", data.message);
                    }
                })
                .catch(error => {
                    console.error("Error submitting rating:", error);
                });
            }
        });
    });

    // Function to highlight stars based on the rating value
    function highlightStars(value) {
        const stars = document.querySelectorAll(".rating-interactive .fa-star");

        stars.forEach(star => {
            const starValue = parseFloat(star.getAttribute("data-value"));
            if (starValue <= value) {   
                star.classList.add("checked");
            } else {
                star.classList.remove("checked");
            }
        });
    }

    // Function to update the display of the user's rating after submission
    function updateUserRatingDisplay(rating) {
        const userStars = document.querySelectorAll(".rating-right .fa-star");

        userStars.forEach(star => {
            const starValue = parseFloat(star.getAttribute("data-value"));
            if (starValue <= rating) {
                star.classList.add("checked");
            } else {
                star.classList.remove("checked");
            }
        });

        // Store user rating for future mouseout action
        const ratingElement = document.querySelector(".rating-interactive");
        if (ratingElement) {
            ratingElement.setAttribute("data-user-rating", rating);
        }
    }

    function updateAverageRatingDisplay(averageRating) {
        // Convert averageRating to a number to ensure it's a valid number
        averageRating = parseFloat(averageRating);

        if (Number.isFinite(averageRating)) {
            const avgStars = document.querySelectorAll(".stars-average .fa-star");

            avgStars.forEach(star => {
                const starValue = parseFloat(star.getAttribute("data-value"));
                if (starValue <= averageRating) {
                    star.classList.add("checked");
                } else {
                    star.classList.remove("checked");
                }
            });

            // Update the average rating text
            const avgText = document.querySelector(".average-rating-text");
            if (avgText) {
                avgText.textContent = `${averageRating.toFixed(1)} / 5`;
            }
        } else {
            console.error("Invalid average rating:", averageRating);
        }
    }
});
