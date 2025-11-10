import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { userService } from "../lib/api/services/user.service"; // Adjust path as needed

const cuisines = [
  "Italian",
  "Indian",
  "Chinese",
  "Mexican",
  "Japanese",
  "French",
  "Thai",
  "Mediterranean",
  "Continental",
  "Korean",
  "Arabic",
  "Other"
];

const UserPreferences = () => {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load existing preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const profile = await userService.getProfile();
        if (profile.preferences?.cuisine_preferences) {
          setSelected(profile.preferences.cuisine_preferences);
        }
      } catch (err) {
        console.error("Error loading preferences:", err);
      } finally {
        setInitialLoading(false);
      }
    };

    loadPreferences();
  }, []);

  const toggleCuisine = (cuisine: string) => {
    if (selected.includes(cuisine)) {
      setSelected(selected.filter((c) => c !== cuisine));
    } else {
      setSelected([...selected, cuisine]);
    }
  };

  const handleSave = async () => {
    if (selected.length === 0) {
      alert("Please select at least one cuisine");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Call the backend API to update preferences
      const updatedUser = await userService.updateProfile({
        preferences: {
          cuisine_preferences: selected,
          dietary_restrictions: [], // You can enhance this later
          cooking_skill: "beginner" // Default value
        }
      });

      // Update localStorage with the response from backend
      localStorage.setItem("user", JSON.stringify(updatedUser));

      alert("Preferences saved successfully!");
      navigate("/");
    } catch (err: any) {
      console.error("Error saving preferences:", err);
      setError(err.response?.data?.detail || "Failed to save preferences");
      alert("Error saving preferences. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-100 via-white to-red-100">
        <div className="bg-white p-10 rounded-2xl shadow-lg">
          <div className="text-gray-600 text-center">Loading preferences...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-100 via-white to-red-100">
      <div className="bg-white p-10 rounded-2xl shadow-lg w-full max-w-lg">
        <h2 className="text-3xl font-bold mb-6 text-center text-orange-600">
          Select Your Favorite Cuisines
        </h2>
        <p className="text-gray-600 mb-5 text-center">
          We will show recipes based on your preferences
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mb-6">
          {cuisines.map((cuisine) => (
            <button
              key={cuisine}
              onClick={() => toggleCuisine(cuisine)}
              disabled={loading}
              className={`px-4 py-2 rounded-xl border transition ${
                selected.includes(cuisine)
                  ? "bg-orange-500 text-white border-orange-500"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-orange-50"
              } ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {cuisine}
            </button>
          ))}
        </div>

        <button
          onClick={handleSave}
          disabled={loading}
          className={`w-full bg-gradient-to-r from-orange-500 to-red-600 text-white py-3 rounded-xl font-semibold hover:from-orange-600 hover:to-red-700 transition-all duration-200 ${
            loading ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {loading ? "Saving..." : "Save Preferences"}
        </button>
      </div>
    </div>
  );
};

export default UserPreferences;