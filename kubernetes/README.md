# Running AI News Aggregator on Local Kubernetes

Follow these steps to deploy and run the news aggregator locally using Minikube or K3s.

## Prerequisites
- **Minikube** installed and running: `minikube start`
- **kubectl** CLI installed.

## Step 1: Configure Secrets
1. Open [secrets.yaml](secrets.yaml) and replace the values under `data:` with your own Base64-encoded secrets.
2. Example to generate a base64 string on Windows PowerShell:
   ```powershell
   [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("YOUR_API_KEY"))
   ```
   Or on Linux/macOS:
   ```bash
   echo -n "YOUR_API_KEY" | base64
   ```

## Step 2: Build the Container Image
Set your terminal environment to point to Minikube's Docker daemon so the image can be resolved locally:
```bash
# For bash/zsh:
eval $(minikube docker-env)

# For PowerShell:
minikube docker-env | Invoke-Expression
```
Now, build the image from the root directory of the repository:
```bash
docker build -t news-aggregator-scraper:latest .
```

## Step 3: Apply the Resources
Apply configuration, secrets, database, and CronJob resources:
```bash
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/cronjob.yaml
```

## Step 4: Verify and Test Trigger
You can manually trigger the CronJob immediately to test the execution:
```bash
kubectl create job --from=cronjob/news-aggregator-scraper news-aggregator-test-run
```
Monitor the logs of the triggered container:
```bash
kubectl logs -f -l job-name=news-aggregator-test-run
```
