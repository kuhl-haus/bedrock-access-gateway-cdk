try {
    Invoke-Expression .\.venv\Scripts\Activate.ps1 -ErrorAction Stop

    cdk ls
    cdk bootstrap
    cdk deploy --all --require-approval never --progress events
}
catch {
    Write-Output $_
}
