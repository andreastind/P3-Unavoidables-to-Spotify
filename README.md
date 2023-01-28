# P3 Unavoidable to Spotify
This project is for automatically maintaining a Spotify playlist containing all
of P3's Ugens Uundgåelige.<br>
<br>
The radio station P3 announces *Ugens Uundgåelige* (The Week's Unavoidable) 
(almost) every Monday, and has done so since 1991. This project scrapes the 
website https://andyg.dk/p3trends/unavoidables/ for information about these 
tracks.<br>
<br>
Once scraped, the data is cleaned. Then, through Spotify's API, track title and 
artist are fuzzy matched with their top 5 Spotify search results. This yields a 
track URI for the best match.  This is stored locally in a csv file together
with the scraped data, updating if changes happens to the website.<br>
<br>
Through the track URIs, a playlist is automatically updated with all tracks in
the csv. See for example: https://open.spotify.com/playlist/4nNezLeeSeQi64oHnDHEX6?si=c0e436ec75e34db9<br>
<br>
### Author
Created by Andreas Tind Damgaard.

