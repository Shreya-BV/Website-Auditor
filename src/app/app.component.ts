import { Component, OnInit, inject } from '@angular/core';
import { Router, NavigationEnd, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs/operators';
import { VisitorService } from './services/visitor.service';
import { HeaderComponent } from './shared/header/header.component';
import { FooterComponent } from './shared/footer/footer.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, HeaderComponent, FooterComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'website-auditor';
  private visitorService = inject(VisitorService);
  private router = inject(Router);

  ngOnInit() {
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      const pageUrl = event.urlAfterRedirects || event.url || '/';
      this.visitorService.trackVisitor(pageUrl).subscribe({
        next: () => {},
        error: (err) => console.error('Failed to log visitor traffic:', err)
      });
    });
  }
}
