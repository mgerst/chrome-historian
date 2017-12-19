[CmdletBinding()]
Param(
    [Parameter(Mandatory=$True)]
    [string]$userListPath = C:\Users\$env:USERNAME\users.csv,

    [Parameter(Mandatory=$True)]
    [string]$historyPath = C:\Users\$env:USERNAME\histories
)

Write-Host -ForegroundColor Yellow "############################################"
Write-Host -ForegroundColor Green "Collect chrome histories in a chrome-historian ready format"

Write-Host -ForegroundColor Yellow "############################################"
Write-Host -ForegroundColor Green "Part 1: Get list of users"
Write-Host -ForegroundColor Yellow "Exporting the list of users to $userListPath"

# List the users in C:\Users and export to the local profile for calling later
dir C:\Users | select Name | Export-Csv -Path $userListPath -NoTypeInformation
$list = Test-Path $userListPath

Write-Host -ForegroundColor Yellow "############################################"
Write-Host -ForegroundColor Green "Part 2: Grabbing Histories"
Write-Host -ForegroundColor Yellow "Writing histories to $historyPath"
$histdb = $historyPath
New-Item $histdb -type directory

if ($list) {
    Import-CSV -Path C:\Users\$env:USERNAME\users.csv -Header Name | foreach {
        Copy-Item "C:\Users\$($_.Name)\AppData\Local\Google\Chrome\User Data\Default\History" "$histdb\$($_.Name)"
    }

    Write-Host -ForegroundColor Green "Done"
} else {
    Write-Host -ForegroundColor Red "User list not found"
    Exit
}
