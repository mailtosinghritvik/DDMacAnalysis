1. We need a function that you can code in the utils folder that will be able to return a table (pandas) of all the : (users here means employees)
    Client, The total time spent by all the users on that client, Start date, End Date, Time spend weekly on the client by all the users total.

2. We need a function that you can code in the utils folder that will be able to return a table (pandas) of all the : (users here means employees)
    Projects inside a specific client, The total time spent by all the users on that project, Start date of each project, End Date, Time spend weekly on the project, by all the users total.

3. We need a function that you can code in the utils folder that will be able to return a table (pandas) of all the : (users here means employees)
   

    YOU CAN SPLIT THIS INTO TWO. 
         the first table will be then (user,start,end,daily average,list of clients,list of projects) 

        naveen| 01-08-2025| 11 -9 2025| 250 (total time by naveen) / 40 (number of days naveen has worked (DO NOT do endDate-startDate, because that will exclude weekends and leaves or holidays, count the days manually)) -> 9| [shlegel,ritvik,blahblah] |[shlegelWiring,shlegelPipes,ritvikCoding,ritvikCigarettes,blahblahTask1,blahblahTask2]



         then for each user there will be a second table which we can do either daily or weekly (TRY BOTH)
         this will be week/day, clients worked on, projects worked on, hours worked on the given C/P. 
         Sometimes a user might work on two projects or clients in one day/week, 
         so you should be able display both, and when we're adding we're adding both together.
         
        
         
        THIS table below is for naveen only

         Week/Day| Client | Project | Hours
         20-12-2025 |Shlegel |  Wiring | 2
         20-12-2025 |Shlegel |  Pipes | 8
         27-12-2025 |ritvik |  Coding | 12
         27-12-2025 |ritvik |  Coding | 15
         2-1-2026 |blahblah |  Task1 | 31
         2-1-2026 |blahblah |  Task2 | 12
 

         
         

4. We need a function that you can code in the utils folder that will be able to return a table (pandas) of all the : (users here means employees)
    Users that have worked on a specific project,
    The start date of project, End date (this will be the last date that the user has checked in on the project),
    Total work done each day by the user on the project,
    Daily work done by each user on the project

    For each project :

    Project|Start|End|ListUsers|
       
 



