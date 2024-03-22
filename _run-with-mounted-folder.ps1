Write-Host "When docker has run an you are at bash inside container, you can do for example:"
Write-Host "python default.py -u https://webperf.se -t 26 -o reports/webperf-se-t-26.json -r"
New-Item -ItemType Directory -Force -Path "$(pwd)\reports\"
docker run -it --mount src="$(pwd)\reports",target=/usr/src/app/reports,type=bind --cap-add=SYS_ADMIN --rm webperf-task-runner:0.0.1 bash