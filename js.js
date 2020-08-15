console.log("hello");

const endpoint =
  "https://volleyballapi.web4data.co.uk/api/competitions/byevent/21";

// jQuery.ajax({
//   url: endpoint,
//   success: function(data){
//     return data
//   }
// })

// x = jQuery.ajax({
//   url: 'https://volleyballapi.web4data.co.uk/api/competitions/byevent/21',
//   success: function(data){
//     return data
//   }
// })

// x = jQuery.ajax('https://volleyballapi.web4data.co.uk/api/competitions/byevent/21')

// x = jQuery.ajax('https://volleyballapi.web4data.co.uk/api/matches/byevent/21')

async function getList() {
  // fetch data from a url endpoint
  const data = await axios.get(
    "https://volleyballapi.web4data.co.uk/api/matches/byevent/21"
  );
  console.log(data);
  GenerateWinnerString(data.data);
}

function GenerateWinnerString(list) {
  for (d of list) {
    if (d.Winner) {
      let bracket = `in ${d.Bracket}`
      let team1 = `(${d.TeamA.Seed}) ${d.TeamA.Captain.FirstName} ${d.TeamA.Captain.LastName}/${d.TeamA.Player.FirstName} ${d.TeamA.Player.LastName}`;
      let team2 = `(${d.TeamB.Seed}) ${d.TeamB.Captain.FirstName} ${d.TeamB.Captain.LastName}/${d.TeamB.Player.FirstName} ${d.TeamB.Player.LastName}`;
      let score1 = "";
      let score2 = "";
      for (ms of d.Sets) {
        score1 += `${ms.A}-${ms.B}, `;
        score2 += `${ms.B}-${ms.A}, `;
      }
      console.log(
        d.Winner === 1
          ? `${team1} ${score1}def ${team2} ${bracket}`
          : `${team2} ${score2}def ${team1} ${bracket}`
      );
    }
  }
}

getList();

