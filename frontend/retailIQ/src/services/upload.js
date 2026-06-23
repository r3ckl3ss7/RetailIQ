import api from "./api";

/**
 * Upload an image file to the backend local storage.
 * @param {File} file - The image file to upload
 * @param {"avatar"|"logo"} type - The upload type
 * @returns {Promise<string>} The URL of the uploaded image
 */
export async function uploadImage(file, type = "avatar") {
  const formData = new FormData();
  formData.append("file", file);

  const endpoint = type === "logo" ? "/upload/logo" : "/upload/avatar";

  const response = await api.post(endpoint, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  // The backend returns { url: "/uploads/avatars/abc.png" }
  // We need to prepend the API base URL to make it a full URL
  const baseUrl = import.meta.env.VITE_API_URL;
  return `${baseUrl}${response.data.url}`;
}
