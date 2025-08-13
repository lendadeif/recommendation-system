using System;
using System.Diagnostics;
using System.IO;
using Newtonsoft.Json;

public class PythonRecommendationService
{
    private readonly string _pythonPath;
    private readonly string _scriptPath;

    public PythonRecommendationService()
    {
        // Configure paths - adjust these for your environment
        _pythonPath = "python"; // or "python3" on Linux/Mac
        _scriptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, 
                                 "recommendation_engine.py");
    }

    public RecommendationResult GetRecommendations(string userId, string[] orderHistory = null)
    {
        // Prepare input data
        var input = new {
            user_id = userId,
            order_history = orderHistory ?? Array.Empty<string>()
        };

        try
        {
            // 1. Configure process start
            var startInfo = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_scriptPath}\" \"{JsonConvert.SerializeObject(input)}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = Path.GetDirectoryName(_scriptPath)
            };

            // 2. Start Python process
            using (var process = new Process { StartInfo = startInfo })
            {
                process.Start();
                
                // 3. Read output
                string output = process.StandardOutput.ReadToEnd();
                string error = process.StandardError.ReadToEnd();
                
                process.WaitForExit();

                // 4. Handle errors
                if (process.ExitCode != 0 || !string.IsNullOrEmpty(error))
                {
                    throw new Exception($"Python error: {error}");
                }

                // 5. Parse and return results
                var result = JsonConvert.DeserializeObject<PythonResponse>(output);
                
                if (!result.Success)
                {
                    throw new Exception(result.Error);
                }

                return new RecommendationResult
                {
                    UserId = result.UserId,
                    Recommendations = result.Recommendations,
                    GeneratedAt = DateTime.Parse(result.GeneratedAt)
                };
            }
        }
        catch (Exception ex)
        {
            // Log error here
            return new RecommendationResult
            {
                Success = false,
                ErrorMessage = ex.Message
            };
        }
    }

    // Response classes
    private class PythonResponse
    {
        public bool Success { get; set; }
        public string UserId { get; set; }
        public int[] Recommendations { get; set; }
        public string GeneratedAt { get; set; }
        public string Error { get; set; }
    }
}

public class RecommendationResult
{
    public bool Success { get; set; } = true;
    public string UserId { get; set; }
    public int[] Recommendations { get; set; }
    public DateTime GeneratedAt { get; set; }
    public string ErrorMessage { get; set; }
}